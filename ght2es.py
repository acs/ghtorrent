#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copy data from GHTorrent to Elasticsearch
#
# Copyright (C) Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#

import argparse
import logging

import pymysql

from elasticsearch import helpers, Elasticsearch

HTTPS_CHECK_CERT = False
NUM_PROJECTS = 0
BULK_CHUNK_SIZE = 10000
GITHUB_URL = "https://github.com"


def get_params():
    parser = argparse.ArgumentParser(usage="usage: ght2es.py [options]",
                                     description="Publish GHTorrent data in Elasticsearch")
    parser.add_argument("-e", "--elastic-url", required=True,
                        help="Elasticsearch URL with the metrics")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-i', '--index', required=True, help='Index to fill with GHTorrent info')
    parser.add_argument('--db-name', default='gh-torrent', help='GHTorrent database (gh-torrent default)')
    parser.add_argument('--db-user', default='root', help='GHTorrent database user (root default)')
    parser.add_argument('--db-passwd', default='', help='GHTorrent database password ("" default)')
    parser.add_argument('--language', default='', help='Programming language to be published')

    return parser.parse_args()

def fetch_projects(es_index, db_con, language=None):
    """
    Fetch projects
    :param es_index: Elasticsearch index in which to publish the data
    :param db_con: connection to GHTorrent database
    :param language: projects programming language to be used
    :return: a dict with the project info to be added to es_index
    """

    global NUM_PROJECTS

    projects_sql = """
        SELECT created_at, name, language, forked_from, url, owner_id, deleted
        FROM projects
    """

    if language:
        projects_sql += ' WHERE language="%s"' % language

    # For removing the forks
    # WHERE forked_from IS NULL
    # For debugging
    # LIMIT 100000
    logging.info("Getting projects: %s" % projects_sql)
    db_cursor = db_con.cursor(pymysql.cursors.SSCursor)
    db_cursor.execute(projects_sql)
    logging.info("SQL query finished")


    for project_row in db_cursor:
        api_url = project_row[4]
        [api, owner, repo] = [None, None, None]
        if api_url:
            [api, owner, repo] = api_url.rsplit("/", 2)
        project_url = GITHUB_URL + "/%s/%s" % (owner, repo)
        project_json = {
            "created_at": project_row[0],
            "name": project_row[1],
            "language": project_row[2],
            "forked_from": project_row[3],
            "api_url": api_url,
            "url": project_url,
            "owner_id": project_row[5],
            "deleted": project_row[6],
        }
        item = {
            "_index": es_index,
            "_type": "item",
            "_source": project_json
        }
        NUM_PROJECTS += 1
        yield item




def publish_projects(es_url, es_index, db_con, language):
    """
    Publish all the scores for the metrics in assessment

    :param es_url: URL for Elasticsearch
    :param es_index: index in Elasticsearch
    :param db_con: connection to GHTorrent database
    :param language: projects programming language to be used
    :return:
    """

    global NUM_PROJECTS

    es_conn = Elasticsearch([es_url], timeout=100, verify_certs=HTTPS_CHECK_CERT)

    NUM_PROJECTS = 0
    helpers.bulk(es_conn, fetch_projects(es_index, db_con, language), chunk_size=BULK_CHUNK_SIZE)
    logging.info("Total projects published in %s: %i", es_index, NUM_PROJECTS)


def db_connect(name, user, passwd, host='localhost', port=3306):
    """
    Connect to the MySQL database.

    :param name: database name
    :param user: database connect user
    :param password: database connect password
    :param host: host in which mysql server is running
    :param port: port in which mysql server is listening
    :return: a connection to the database
    """
    """
    """

    try:
        db = pymysql.connect(user=user, passwd=passwd,
                             host=host, port=port,
                             db=name, use_unicode=True)
        return db
    except Exception:
        logging.error("Database connection error")
        raise


if __name__ == '__main__':

    args = get_params()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
        logging.debug("Debug mode activated")
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    db_con = db_connect(args.db_name, args.db_user, args.db_passwd)

    publish_projects(args.elastic_url, args.index, db_con, args.language)
