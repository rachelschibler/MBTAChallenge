import http.client, json
import sys
import route, stop
from itertools import groupby


def get_data_from_api(url):
    """Makes a 'get' request based on the input URL and returns 
    the retrieved data in the form of a list. Helper function 
    accessed by the create_route_and_stop_data_structures function"""

    # Connect to MBTA API (https://api-v3.mbta.com/docs/swagger/index.html)
    connection = http.client.HTTPSConnection('api-v3.mbta.com')

    # Make a GET request 
    connection.request('GET', url)
    response = connection.getresponse()

    # If status of response is not good, print an error and exit the program
    if response.status != 200:
        print("ERROR: Response Status: {}, Reason: {}".format(response.status,response.reason))
        sys.exit()
    
    data_bin = response.read()
    connection.close()

    # Convert binary data to a list and return 
    data_l = json.loads(data_bin.decode('utf-8'))['data']
    return data_l
    

def create_route_and_stop_data_structures():
    """Creates and returns a list of Route objects and a dictionary of Stop objects 
    based on the subway data rerieved from the MBTA API but reduced to the salient data"""
    
    # Filter route data by type 0,1 to retrieve only subway routes 
    # and only include 'long_name' attribute to reduce request size
    url = '/routes?filter[type]=0,1&fields[route]=long_name'
    route_data = get_data_from_api(url)

    route_objs = [] # List to contain all subway Route objects 
    stop_objs = {} # Dictionary to contain all subway Stop objects, with the name as the key 
    for r in route_data:

        ############### Append to Route list ################

        route_id = r['id']
        route_name = r['attributes']['long_name']

        # Get stop data for each route (a specific route ID must
        # be referenced in order to get stop data with the route)
        url = '/stops?include=route&filter[route]={}'.format(route_id)
        stop_data = get_data_from_api(url)

        num_stops = len(stop_data)

        # Append new Route to list
        route_objs.append(route.Route(route_id,route_name,num_stops))

        ############### Add to Stop dictionary ################
        # Loop through all stops for each route, and create a dictionary entry for each new Stop. 
        # Note: stops are listed in route-order.
        for s_ind in range(len(stop_data)):
            
            s = stop_data[s_ind]
            stop_id = s['id']
            stop_name = s['attributes']['name']

            # If stop not yet in dictionary, add it
            if stop_name not in stop_objs:
                stop_objs[stop_name] = stop.Stop(stop_id,stop_name)

            # Add the route to the stop's list of routes
            stop_objs[stop_name].add_route(route_name)

            # Add the connections to the stop's list of connections
            if s_ind != 0: #if not first stop in route, add previous stop connection
                prev_stop_name = stop_data[s_ind-1]['attributes']['name']
                stop_objs[stop_name].add_connection((prev_stop_name,route_name))
            if s_ind != len(stop_data)-1: #if not last stop in route, add next stop connection
                next_stop_name = stop_data[s_ind+1]['attributes']['name']
                stop_objs[stop_name].add_connection((next_stop_name,route_name))

    return route_objs, stop_objs


def print_route_names(route_objs):
    """Prints long names of each Route in the input list of subway Routes"""

    print('\nSubway Routes: ')
    for r in route_objs:
        print(r.name)
    

def print_stop_names(stop_objs):
    """Prints names of each Stop in the input dictionary of subway Stops"""

    print('\nSubway Stops:\n{}'.format('\n'.join(list(stop_objs.keys()))))


def print_route_most_least_stops(route_objs):
    """Prints the name of the subway route in the input Route list with the most stops 
    and its number of stops. If multiple routes have the most or least number of stops, 
    prints only the first one in the list."""
    
    # If route list is empty, return without printing 
    if not route_objs: 
        return  

    # Find Routes with the most and least number of stops by comparing num_stops of each Route in list
    most_temp = route_objs[0] # Route with the most stops so far (initialize with first route)
    least_temp = route_objs[0] # Route with the least stops so far (initialize with first route)
    for r in route_objs: 
        if r.num_stops > most_temp.num_stops: 
            most_temp = r
        if r.num_stops < least_temp.num_stops:
            least_temp = r
    print('\nSubway route with the most stops is {} with {} stops'.format(most_temp.name,most_temp.num_stops))
    print('Subway route with the least stops is {} with {} stops'.format(least_temp.name,least_temp.num_stops))
    

def print_stops_with_multiple_routes(stop_objs):
    """Prints the name of the stop in the input Stop dictionary that multiple subway routes visit"""

    print('\nStops that connect multiple subway routes: ')
    for s in list(stop_objs.values()):
        # If there's more than 1 route that visits the stop, print the stop name and the route names
        if len(s.routes) > 1: 
            print('{} (Routes: {})'.format(s.name,', '.join(s.routes)))


def get_stop_name(start_or_end,stop_objs): 
    """Prompts user to input a stop name and returns the stop name. If user inputs 'options',
    function prints a list of all subway stops. If user input's 'quit', program will stop running.
    Input String start_or_end specifies whether user is inputting first or last stop on desired route. 
    Also takes as input a dictionary of Stop objects. Helper function for get_start_end_stop_names."""

    # Get user input 
    stop_name = input("\nEnter the {}ing stop name (or enter 'options' to list all stops or \
        'quit' to exit): ".format(start_or_end))

    # If user specifies 'quit', exit the program 
    if stop_name.lower() == 'quit':
        sys.exit()

    # If user specifies 'options', list all stops and re-prompt user
    if stop_name.lower() == 'options':
        print_stop_names(stop_objs)
        stop_name = get_stop_name(start_or_end,stop_objs)

    # If input is not a valid stop name, print error and re-prompt user
    elif stop_name not in list(stop_objs.keys()):
        print("Error: The stop entered is invalid. Try again. Note: input is case-sensitive")
        stop_name = get_stop_name(start_or_end,stop_objs)

    return stop_name


def get_start_end_stop_names(stop_objs):
    """Get start and end stop names from user by calling get_stop_name function
    twice, and return both string stop names."""

    start_stop_name = get_stop_name("start",stop_objs)
    end_stop_name = get_stop_name("end",stop_objs)
    return start_stop_name, end_stop_name


def find_all_paths_connecting_stops(start_stop_name,end_stop_name,stop_objs,route_l,stop_l,all_paths):
    """Recursive function for finding all (non-redundant) paths (ordered list of 
    routes) between the input start and end stop. Non-redundant in this case means that if a 
    stop is already visited on the path so far, don't recursively call in that direction."""

    # If we've reached the end stop, append the path (route list) to the list of all paths
    if start_stop_name == end_stop_name:
        all_paths.append(route_l)
    else:
        start_stop = stop_objs[start_stop_name]
        # Loop through all connections of current start stop
        for conn in start_stop.connections:
            # If haven't visited the connecting stop already in the current path (prevents 
            # infinite loops and redundant paths)
            if conn[0] not in stop_l:
                # Add the stop to the list of visited stops
                new_stop_l = stop_l + [conn[0]]
                # Add the route to the current path 
                new_route_l = route_l + [conn[1]]
                # Recursively call the function with the connecting stop as the new starting stop
                find_all_paths_connecting_stops(conn[0],end_stop_name,stop_objs,new_route_l,new_stop_l,all_paths)
    

def get_best_path(start_stop_name,end_stop_name,stop_objs):
    """Finds and returns (for testing) the path (list of routes) with the least 
    number of route transfers between the input start and end stops."""

    # Get all (non-stop-redundant) paths connecting input start and end stops
    all_paths = []
    find_all_paths_connecting_stops(start_stop_name,end_stop_name,stop_objs,[],[start_stop_name],all_paths)
    
    # If no path exists to connect the two stops, print message and return 
    if not all_paths:
        print("There exists no route that connects {} and {}".format(start_stop_name,end_stop_name))
        return 
    
    best_path = all_paths[0] #Path with least route-transfers so far (initialize with first path)
    for path in all_paths:
        # Remove any route in path that is consecutively redundant (ie [Red,Red,Green] -> [Red,Green]), 
        # since it's understood the passenger would stay on that route. Length of reduced_path then 
        # basically represents number of route transfers.
        reduced_path = [i[0] for i in groupby(path)]
        # Compare number of route transfers in each path to find the one with the minimal number
        if len(reduced_path) < len(best_path):
            best_path = reduced_path

    return best_path

def print_best_path(start_stop_name, end_stop_name, best_path):
    """ Prints the path with the least number of route transfers from the start stop to 
    the end stop, as found by the get_best_path function"""
    print("\nA route from {} to {}: {}".format(start_stop_name,end_stop_name,", ".join(best_path)))
        
    
if __name__ == "__main__":

    # Retrieve list of route objects and dictionary of stop objects
    route_objs, stop_objs = create_route_and_stop_data_structures() 

    # Q1: Print long names of routes
    print_route_names(route_objs)

    # Q2.1 & Q2.2: Print routes with most and least stops
    print_route_most_least_stops(route_objs)
    # Q2.3: List stops that connect 2+ routes
    print_stops_with_multiple_routes(stop_objs)

    # Q3: List rail route from user input stop 1 to stop 2
    start_stop_name, end_stop_name = get_start_end_stop_names(stop_objs)
    best_path = get_best_path(start_stop_name,end_stop_name,stop_objs)
    print_best_path(start_stop_name,end_stop_name,best_path)

