#!/usr/bin/env python
"""
Module for updating corp information. If this is ran directly, the module will
iterate through all known alliances, looking at the corps in each alliance's
member list. This can be very time-consuming and should not be done often.

Within your applications, you may call query_and_update_corp() to update
an individual corp object as need be.

NOTE: To get corp data, it must be a member of an alliance.
"""

if __name__ == "__main__":
    # Only mess with the environmental stuff if this is being ran directly.
    from importer_path import fix_environment
    fix_environment() 

from eve_api.models import EVEPlayerAlliance, EVEPlayerCorporation

def start_full_import():
    """
    Imports all of the corps that are in all of the known alliances.
    
    WARNING: THIS WILL TAKE A _LONG_ TIME AND MUST BE RAN AFTER
    eve_db.api_puller.alliances.__start_full_import() OR YOU WON'T GET ALL
    OF THE CORPS (or any at all).
    """
    alliances = EVEPlayerAlliance.objects.all()
    
    # These two variables are used to track progress.
    alliance_count = alliances.count()
    # Use this as a progress indicator.
    current_alliance_num = 1
    
    for alliance in alliances:
        # Keep the user informed as to the progress.
        print "Alliance %d of %d..." % (current_alliance_num, alliance_count)
        # A list of the alliance's member corps.
        member_corps = alliance.eveplayercorporation_set.all()
        # We're getting the list of corps to update from alliance memberships.
        for corp in member_corps:
            print "Querying", corp.id
            corp.query_and_update_corp()
            
        # Increment progress counter.
        current_alliance_num += 1
    
if __name__ == "__main__":
    """
    If ran directly, this will grab all of the corps from the known alliances.
    
    WARNING: THIS WILL TAKE A VERY LONG TIME TO RUN! IT IS SUGGESTED YOU ONLY
    GRAB CORPS AS YOU NEED THEM.
    """
    start_full_import()