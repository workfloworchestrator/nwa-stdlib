from werkzeug.exceptions import Forbidden
import sys
import fnmatch


class InvalidRuleDefinition(Exception):
    def __str__(self):
        return "{} (rule {}):\n{}".format(*self.args)


class AbstractCondition(object):

    @classmethod
    def concrete_condition(klass, name, options):
        subclasses = {subclass.__name__: subclass for subclass in klass.__subclasses__()}
        my_condition = subclasses[name](options)
        return my_condition


class TargetOrganizations(AbstractCondition):
    URN = "urn:mace:surfnet.nl:surfnet.nl:sab:organizationCode:"
    institutions = set([1, 2, 4, 5, 8, 9, 14, 15, 16, 18, 19, 21, 22, 23, 24, 100])
    service_providers = set([11])
    international_partners = set([13])
    all = institutions | service_providers | international_partners

    valid = {
        'institutions': institutions,
        'service_providers': service_providers,
        'international_partners': international_partners,
        'all': all}

    def __init__(self, options):
        self.target_organizations = set.union(*[self.valid[option] for option in options])

    def __str__(self):
        return f"CODE in {self.URN}CODE in eduperson_entitlements should be one of {sorted(self.target_organizations)}"

    def test(self, user_attributes, current_request):
        return bool(user_attributes.organization_codes & self.target_organizations)


class SABRoles(AbstractCondition):
    URN = "urn:mace:surfnet.nl:surfnet.nl:sab:role:"
    infrabeheerder = "Infrabeheerder"
    infraverantwoordelijke = "Infraverantwoordelijke"

    valid = {
        'infrabeheerder': infrabeheerder,
        'infraverantwoordelijke': infraverantwoordelijke,
        'Infrabeheerder': infrabeheerder,
        'Infraverantwoordelijke': infraverantwoordelijke}

    def __init__(self, options):
        self.roles = {self.valid[option] for option in options}

    def __str__(self):
        return f"ROLE in {self.URN}ROLE in eduperson_entitlements should be one of {self.roles}"

    def test(self, user_attributes, current_request):
        return bool(user_attributes.roles & self.roles)


class Teams(AbstractCondition):
    URN = "urn:collab:group:surfteams.nl:nl:surfnet:diensten:"
    superuserro = "noc_superuserro_team_for_netwerkdashboard"
    noc = "noc-engineer"
    klantsupport = "nwa-automation-klantsupport"
    changes = "nwa-automation-network-changes"

    valid = {
        'superuserro': superuserro,
        'noc': noc,
        'klantsupport': klantsupport,
        'changes': changes}

    def __init__(self, options):
        self.teams = {self.valid[option] for option in options}

    def __str__(self):
        return f"TEAM in {self.URN}TEAM should be one of {self.teams}"

    def test(self, user_attributes, current_request):
        return bool(user_attributes.teams & self.teams)


class AnyOf(AbstractCondition):

    def __init__(self, options):
        self.conditions = [AbstractCondition.concrete_condition(name, suboptions) for name, suboptions in options.items()]

    def __str__(self):
        lst = "\n".join(str(c) for c in self.conditions)
        return f"Any of the following conditions should apply:\n{lst}"

    def test(self, user_attributes, current_request):
        return True in (condition.test(user_attributes, current_request) for condition in self.conditions)


class AllOf(AbstractCondition):

    def __init__(self, options):
        self.conditions = [AbstractCondition.concrete_condition(name, suboptions) for name, suboptions in options.items()]

    def __str__(self):
        lst = "\n".join(str(c) for c in self.conditions)
        return f"All of the following conditions should apply:\n{lst}"

    def test(self, user_attributes, current_request):
        return False not in (condition.test(user_attributes, current_request) for condition in self.conditions)


class OrganizationGUID(AbstractCondition):
    URN = "urn:mace:surfnet.nl:surfnet.nl:sab:organizationGUID:"
    valid = {"path", "query", "json"}

    def __init__(self, options):
        assert options["where"] in self.valid, f"The 'where' option should be one of {self.valid}"
        self.where = options["where"]
        self.param = options["parameter"]

    def __str__(self):
        return f"Parameter {self.param} in the request {self.where} should be in your organization GUID ('{self.URN}')"

    def test(self, user_attributes, current_request):
        if self.where == "path":
            return current_request.view_args.get(self.param) in user_attributes.organization_guids
        if self.where == "query":
            return current_request.args.get(self.param) in user_attributes.organization_guids
        if self.where == "json":
            json = current_request.json
            if json is None:
                # Let the application handle the bad json request
                return True
            return json.get(self.param) in user_attributes.organization_guids


class UserAttributes(object):

    def __init__(self, oauth_attrs):
        self.oauth_attrs = oauth_attrs

    def __json__(self):
        return self.oauth_attrs

    def __str__(self):
        return str(self.oauth_attrs)

    def __getitem__(self, item):
        return self.oauth_attrs[item]

    @property
    def active(self):
        return self.oauth_attrs.get("active", False)

    @property
    def authenticating_authority(self):
        return self.oauth_attrs.get("authenticating_authority", "")

    @property
    def display_name(self):
        return self.oauth_attrs.get("display_name", "")

    @property
    def principal_name(self):
        return self.oauth_attrs.get("edu_person_principal_name", "")

    @property
    def email(self):
        return self.oauth_attrs.get("email", "")

    @property
    def memberships(self):
        return self.oauth_attrs.get("edumember_is_member_of", [])

    @property
    def entitlements(self):
        return self.oauth_attrs.get("eduperson_entitlement", [])

    @property
    def roles(self):
        prefix = SABRoles.URN
        return {urn[len(prefix):] for urn in self.entitlements if urn.startswith(prefix)}

    @property
    def teams(self):
        prefix = Teams.URN
        return {urn[len(prefix):] for urn in self.memberships if urn.startswith(prefix)}

    @property
    def organization_codes(self):
        prefix = TargetOrganizations.URN
        return {int(urn[len(prefix):]) for urn in self.entitlements if urn.startswith(prefix)}

    @property
    def organization_guids(self):
        prefix = OrganizationGUID.URN
        return {urn[len(prefix):] for urn in self.entitlements if urn.startswith(prefix)}


class AccessControl(object):

    VALID_HTTP_METHODS = {'*', 'DELETE', 'PATCH', 'GET', 'HEAD', 'POST', 'PUT'}

    def __init__(self, security_definitions):
        self.security_definitions = security_definitions

        self.rules = []
        if security_definitions is None or 'rules' not in security_definitions:
            return

        for counter, definition in enumerate(self.security_definitions['rules']):
            try:
                endpoint = definition['endpoint']
            except KeyError:
                raise InvalidRuleDefinition("Missing endpoint", counter, definition)

            try:
                http_methods = definition['methods']
            except KeyError:
                raise InvalidRuleDefinition("Missing HTTP methods", counter, definition)

            for http_method in http_methods:
                if http_method not in self.VALID_HTTP_METHODS:
                    raise InvalidRuleDefinition(f"Not a valid HTTP method '{http_method}'", counter, definition)

            try:
                conditions = definition['conditions']
            except KeyError:
                raise InvalidRuleDefinition("Missing conditions or options", counter, definition)

            checkers = []
            for name, options in conditions.items():
                try:
                    checkers.append(AbstractCondition.concrete_condition(name, options))
                except KeyError as exc:
                    message = f"Missing option {exc}. Could not process condition: {name}: {options}"
                    raise InvalidRuleDefinition(message, counter, definition)
                except AssertionError as exc:
                    message = str(exc)
                    raise InvalidRuleDefinition(message, counter, definition)

            self.rules.append((endpoint, http_methods, checkers))

    def is_allowed(self, current_user, current_request):
        if not self.rules:
            return

        if isinstance(current_user, UserAttributes):
            user_attributes = current_user
        else:
            user_attributes = UserAttributes(current_user)

        endpoint = current_request.endpoint or current_request.base_url
        method = current_request.method

        for endpoint_pattern, http_methods, conditions in self.rules:
            if fnmatch.fnmatch(endpoint, endpoint_pattern):
                if "*" in http_methods or method in http_methods:
                    for condition in conditions:
                        allowed = condition.test(user_attributes, current_request)
                        if not allowed:
                            raise Forbidden(str(condition))
