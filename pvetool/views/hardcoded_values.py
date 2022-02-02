# Some hardcoded values that maps names of statuses to their id's, and defines the "Later" status category.

def later_status_category():
    return ["uitwerken in TO", "uitwerken in UO", "uitwerken in DO", "ontwerp uitgangspunt"]

def status_id_later_status():
    return [4, 5, 6, 7]


def status_to_id():
    return {
        "extra t.o.v. basisprijs": 9,
        "n.v.t.": 8,
        "uitwerken in UO": 7,
        "uitwerken in TO": 6,
        "uitwerken in DO": 5,
        "ontwerp uitgangspunt": 4,
        "niet akkoord": 3,
        "akkoord": 2,
        "n.t.b.": 1,
        "Later uitwerken": 0
    }
    
def later_status_category_name():
    return "Later uitwerken"
