"""
This is strongly based on https://gist.github.com/unbracketed/3380407;
thanks to @unbracketed and the various commenters on the page.

I've mainly cleaned up the code into basic methods, and included the
various suggestions in the comments. Hope this is useful to someone.

Make sure you have `requests` and `csv` installed via pip then run it:
`python export_gh_issues_to_csv.py`

---

Exports Issues from a specified repository to a CSV file
Uses basic authentication (Github username + password) or token to retrieve Issues
from a repository that username has access to. Supports Github API v3.
"""

import csv
import requests

GITHUB_USER = ''
GITHUB_PASSWORD = ''
GITHUB_TOKEN = ''
REPO = ''  # format is username/repo
ISSUES_FOR_REPO_URL = 'https://api.github.com/repos/%s/issues' % REPO

# Update your filter here.  See https://developer.github.com/v3/issues/#list-issues-for-a-repository
# Note that filtering is powerful and there are lots of things available. Also that issues and PRs
# arrive in the same results set
params_payload = {'filter' : 'all', 'state' : 'open', 'type': 'issue' }

def write_issues(response, csvout):
    "output a list of issues to csv"
    print "  : Writing %s issues" % len(response.json())
    for issue in response.json():
        labels = issue['labels']
        label_string = ''
        for label in labels:
            label_string = "%s, %s" % (label_string, label['name'])
        label_string = label_string[2:]

        csvout.writerow([issue['number'], issue['title'].encode('utf-8'), issue['body'].encode('utf-8'), label_string.encode('utf-8'), issue['created_at'], issue['updated_at']])


def get_issues(url):
    kwargs = {
        'headers': {
            'Content-Type': 'application/vnd.github.v3.raw+json',
            'User-Agent': 'GitHub issue exporter'
        },
        'params': params_payload
    }
    if GITHUB_TOKEN != '':
        kwargs['headers']['Authorization'] = 'token %s' % GITHUB_TOKEN
    else:
        kwargs['auth'] = (GITHUB_USER, GITHUB_PASSWORD)

    print "GET %s" % url
    resp = requests.get(url, **kwargs)
    print "  : => %s" % resp.status_code

    # import ipdb; ipdb.set_trace()
    if resp.status_code != 200:
        raise Exception(resp.status_code)

    return resp


def next_page(response):
    #more pages? examine the 'link' header returned
    if 'link' in response.headers:
        pages = dict(
            [(rel[6:-1], url[url.index('<')+1:-1]) for url, rel in
                [link.split(';') for link in
                    response.headers['link'].split(',')]])
        # import ipdb; ipdb.set_trace()
        if 'last' in pages and 'next' in pages:
            return pages['next']

    return None


def process(csvout, url=ISSUES_FOR_REPO_URL):
    resp = get_issues(url)
    write_issues(resp, csvout)
    next_ = next_page(resp)
    if next_ is not None:
        process(csvout, next_)


def main():
    csvfile = '%s-issues.csv' % (REPO.replace('/', '-'))
    csvout = csv.writer(open(csvfile, 'wb'))
    csvout.writerow(('id', 'Title', 'Body', 'Labels', 'Created At', 'Updated At'))
    process(csvout)
    csvfile.close()



main()
