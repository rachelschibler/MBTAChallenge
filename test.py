import unittest
import interfaceMBTA

class TestPaths(unittest.TestCase):

    def test_best_path(self):
        """Runs a few simple tests for the get_best_path function"""

        # Retrieve list of route objects and dictionary of stop objects
        route_objs, stop_objs = interfaceMBTA.create_route_and_stop_data_structures() 

        start_stop_name = 'Davis'
        end_stop_name = 'Davis'
        best_path = interfaceMBTA.get_best_path(start_stop_name,end_stop_name,stop_objs)
        self.assertEqual(best_path, [])

        start_stop_name = 'Davis'
        end_stop_name = 'Kendall/MIT'
        best_path = interfaceMBTA.get_best_path(start_stop_name,end_stop_name,stop_objs)
        self.assertEqual(best_path, ['Red Line'])

        start_stop_name = 'Kendall/MIT'
        end_stop_name = 'Davis'
        best_path = interfaceMBTA.get_best_path(start_stop_name,end_stop_name,stop_objs)
        self.assertEqual(best_path, ['Red Line'])

        start_stop_name = 'Ashmont'
        end_stop_name = 'Arlington'
        best_path = interfaceMBTA.get_best_path(start_stop_name,end_stop_name,stop_objs)
        self.assertEqual(best_path, ['Red Line','Green Line B'])

        start_stop_name = 'Arlington'
        end_stop_name = 'Ashmont'
        best_path = interfaceMBTA.get_best_path(start_stop_name,end_stop_name,stop_objs)
        self.assertEqual(best_path, ['Green Line B','Red Line'])

if __name__ == '__main__':
    unittest.main()