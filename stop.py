class Stop:

    def __init__(self, id_code, name):
        self.id_code = id_code
        self.name = name
        self.routes = []
        self.connections = []
    
    def add_route(self,route):
        self.routes.append(route)

    def add_connection(self,connection):
        self.connections.append(connection)
    