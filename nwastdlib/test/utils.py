import flask


def create_test_app():
    app = flask.Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = 'secret'
    app.debug = True

    @app.route("/hello", methods=['GET', 'POST', 'DELETE'])
    def hello():
        return "hello"

    @app.route("/config")
    def config():
        return "config"

    @app.errorhandler(401)
    def unauthorized(e):
        return flask.jsonify(error=401, detail=str(e)), 401

    @app.errorhandler(403)
    def forbidden(e):
        return flask.jsonify(error=403, detail=str(e)), 403

    return app
