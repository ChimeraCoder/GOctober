import webapp2
import logging

from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import deferred

from gae_django.auth.models import User

from july.people.models import Commit, Location
from july import settings

class CommitCron(webapp2.RequestHandler):
    
    def get(self):
        """
        Search through all the orphan commits and kick off a
        deferred task to re-associate them.
        """  
        deferred.defer(fix_orphans)

def fix_orphans(cursor=None):
    
    if cursor:
        cursor = Cursor(urlsafe=cursor)
        
    query = Commit.query()
    models, next_cursor, more = query.fetch_page(500, keys_only=True, start_cursor=cursor)
    
    for commit in models:
        if commit.parent() is None:
            logging.info("Found orphan commit: %s", commit)
            deferred.defer(fix_commit, commit.urlsafe())
    
    # if we have more keep looping
    if more:
        deferred.defer(fix_orphans, cursor=next_cursor.urlsafe())

def fix_commit(key):
    """Fix an individual commit if possible."""
    commit_key = ndb.Key(urlsafe=key)
    commit = commit_key.get()
    commit_data = commit.to_dict()
    
    # Check the timestamp to see if we should reject/delete 
    if commit.timestamp is None:
        logging.warning("Skipping early orphan")
        return
    
    if commit.timestamp < settings.START_DATETIME:
        logging.warning("Skipping early orphan")
        return
        
    if 'project_slug' in commit_data: 
        del commit_data['project_slug']
    
    new_commit = Commit.create_by_email(commit.email, [commit_data], project=commit.project)
    
    if new_commit and new_commit[0].parent():
        logging.info('Deleting orphan')
        commit.key.delete()

class FixAccounts(webapp2.RequestHandler):
    """Add 'own:username' to all accounts to replace the username property."""
    
    def get(self):
        deferred.defer(fix_accounts)

def fix_accounts(cursor=None):
    """Fix all the accounts in chunks"""
    
    if cursor:
        cursor = Cursor(urlsafe=cursor)
        
    query = User.query()
    models, next_cursor, more = query.fetch_page(15, start_cursor=cursor)
    
    for account in models:
        username = getattr(account, 'username', None)
        if username is None:
            logging.error('No user name set for: %s', account)
            continue
        
        added, _ = account.add_auth_id('own:%s' % username)
        if not added:
            logging.error("Unable to add username: %s", account.username)
            
    if more:
        deferred.defer(fix_accounts, cursor=next_cursor.urlsafe())

class FixLocations(webapp2.RequestHandler):
    
    def get(self):
        """Calculate the total points for each location."""
        deferred.defer(fix_locations)

def fix_locations(cursor=None):
    """Look up all the locations and re-count totals."""
        
    if cursor:
        cursor = Cursor(urlsafe=cursor)

    query = Location.query()
    models, next_cursor, more = query.fetch_page(15, start_cursor=cursor)

    for location in models:
        deferred.defer(fix_location, location.key.urlsafe())
    
    if more:
        deferred.defer(fix_locations, cursor=next_cursor.urlsafe())

def fix_location(key, cursor=None, total=0):
    
    location_key = ndb.Key(urlsafe=key)
    location = location_key.get()
    location_p = getattr(location, 'projects', [])
    projects = set(location_p)
    
    if cursor:
        cursor = Cursor(urlsafe=cursor)
    
    people = User.query().filter(User.location_slug == location.key.id())
    
    # Go through the users in chucks
    models, next_cursor, more = people.fetch_page(100, start_cursor=cursor)
    
    for model in models:
        commits = Commit.query(ancestor=model.key).count(1000)
        total += commits
        user_projects = getattr(model, 'projects', [])
        projects.update(user_projects)
    
    
    # Run update in a transaction
    # if total is zero the list of projects should be
    # cleared as well.
    if not total:
        projects = set([])
        
    projects = list(projects)
    total = total + (len(projects) * 10)
    @ndb.transactional
    def txn():
        location = location_key.get()
        location.total = total
        location.projects = projects
        location.put()
    
    txn()

    if more:
        # We have more people to loop through!!
        return deferred.defer(fix_location, key, 
            cursor=next_cursor.urlsafe(), total=total)

###
### Setup the routes for the Crontab
###
routes = [
    webapp2.Route('/__cron__/commits/', CommitCron),
    webapp2.Route('/__cron__/accounts/', FixAccounts),
    webapp2.Route('/__cron__/locations/', FixLocations),
] 

# The Main Application
app = webapp2.WSGIApplication(routes)