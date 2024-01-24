from __future__ import annotations
import hashlib
import os
from datetime import datetime
from flask import Flask, Response, redirect, render_template, request, session, url_for, flash, jsonify
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
import requests
import json

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config["SESSION_PERMANENT"] = True


class QueryAPI:

    def __init__(self):
        self.media_normal_search = '''
            query (
                $page: Int,
                $search: String,
                $popularity_lesser: Int,
                $popularity_greater: Int,
                $averageScore_lesser: Int,
                $averageScore_greater: Int,
                $sort: [MediaSort],
                $format: MediaFormat, 
                $genre_in: [String],
                $genre_not_in: [String],
                $source: MediaSource,
                $season: MediaSeason,
                $startDate_greater: FuzzyDateInt,
                $startDate_lesser: FuzzyDateInt,
                $episodes_greater: Int,
                $episodes_lesser: Int,
            ) {
                Page (page: $page, perPage: 50) {
                    pageInfo {
                        total
                        currentPage
                        lastPage
                        hasNextPage
                        perPage
                    }
                    media (
                        search: $search,
                        popularity_lesser: $popularity_lesser, 
                        popularity_greater: $popularity_greater, 
                        averageScore_lesser: $averageScore_lesser, 
                        averageScore_greater: $averageScore_greater, 
                        episodes_lesser: $episodes_lesser, 
                        episodes_greater: $episodes_greater,
                        type: ANIME, 
                        sort: $sort, 
                        isAdult: false, 
                        format: $format, 
                        genre_in: $genre_in, 
                        genre_not_in: $genre_not_in,
                        source: $source,
                        season: $season,
                        startDate_greater: $startDate_greater,
                        startDate_lesser: $startDate_lesser,
                        
                    ) {
                        id
                        popularity
                        averageScore
                        trending
                        favourites
                        episodes
                        duration
                        format
                        title {
                            romaji
                            english
                            native
                        }
                        coverImage {
                            extraLarge
                            large
                            medium
                            color
                        }
                        relations {
                            edges {
                                relationType (version: 2)
                            }
                        }
                        startDate {
                            year
                            month
                            day
                        }
                        siteUrl
                        rankings {
                            rank
                            allTime
                            type
                        }
                        stats {
                            statusDistribution {
                                status
                                amount
                            }
                        }
                    }
                }
            }
            '''
        self.media_studio_search = '''
            query (
                $page: Int, 
                $perPage: Int, 
                $studioName: String,
                $animePage: Int, 
                $sort: [MediaSort],
            ) {
                Page (page: $page, perPage: 1) {
                    pageInfo {
                        total
                        currentPage
                        lastPage
                        hasNextPage
                        perPage
                    }
                    studios (search: $studioName) {
                        media (
                            page: $animePage, perPage: $perPage, sort: $sort
                        ) {
                            nodes {
                                id
                                popularity
                                averageScore
                                trending
                                favourites
                                episodes
                                duration
                                genres
                                season
                                seasonYear
                                format
                                title {
                                    romaji
                                    english
                                }
                                coverImage {
                                    extraLarge
                                    large
                                    medium
                                    color
                                }
                                relations {
                                    edges {
                                        relationType
                                    }
                                }
                                siteUrl
                                rankings {
                                    rank
                                    allTime
                                    type
                                }
                                startDate {
                                    year
                                    month
                                    day
                                }
                                stats {
                                    statusDistribution {
                                        status
                                        amount
                                    }
                                }
    
                            }
    
                        }
    
                    }
    
                }
            }
            '''

        self.staff_query = '''
            query (
                $page: Int, 
                $perPage: Int, 
                $sort: [StaffSort]
            ) {
                Page (page: $page, perPage: $perPage) {
                    pageInfo {
                        total
                        currentPage
                        lastPage
                        hasNextPage
                        perPage
                    }
                    staff (
                        sort: $sort,
                    ) {
                        id
                        favourites
                        primaryOccupations
                        image {
                            large
                        }
                        name {
                            full
                        }
                        
                    }
                    
                }
    
            }
            '''
        self.staff_anime_query = '''
                query (
                    $staffID: Int,
                    $page: Int, 
                    $sort: [MediaSort],
                ) {
                    Page (page: 1, perPage: 1) {
                        pageInfo {
                            total
                            currentPage
                            lastPage
                            hasNextPage
                            perPage
                        }
                        staff (
                            id: $staffID,
                        ) {
                            id
                            favourites
                            primaryOccupations
                            image {
                                large
                            }
                            name {
                                full
                            }
                            staffMedia (
                                page: $page, perPage: 50, sort: $sort
                            ) {
                                edges {
                                    staffRole
                                    node {
                                        id
                                        popularity
                                        averageScore
                                        trending
                                        favourites
                                        episodes
                                        duration
                                        genres
                                        season
                                        seasonYear
                                        format
                                        title {
                                            romaji
                                            english
                                            native
                                        }
                                        coverImage {
                                            extraLarge
                                            large
                                            medium
                                            color
                                        }
                                        relations {
                                            edges {
                                                relationType
                                            }
                                        }
                                        siteUrl
                                        rankings {
                                            rank
                                            allTime
                                            type
                                        }
                                        startDate {
                                            year
                                            month
                                            day
                                        }
                                        stats {
                                            statusDistribution {
                                                status
                                                amount
                                            }
                                        }
                                    }
                                }
                            }
                        }
    
                    }
    
                }
                '''
        self.staff_character_query = '''
            query (
                $staffID: Int,
                $page: Int, 
                $sort: [CharacterSort],
            ) {
                Page (page: 1, perPage: 1) {
                    pageInfo {
                        total
                        currentPage
                        lastPage
                        hasNextPage
                        perPage
                    }
                    staff (
                        id: $staffID,
                    ) {
                        id
                        favourites
                        primaryOccupations
                        image {
                            large
                        }
                        name {
                            full
                        }
                        characters (
                            page: $page, perPage: 25, sort: $sort,
                        ) {
                            edges {
                                node {
                                    name {
                                        full
                                    }
                                    image {
                                        large
                                    }
                                }
                                media {
                                    title {
                                        romaji
                                        english
                                        native
                                    }
                                }
                            }
                        }
                    }
    
                }
    
            }
            '''

    def get_anime(self, data_variables):
        manual_searchs = ['distrabutionStatusGreaterThan', 'distrabutionStatusLesserThan', 'includeRelations', 'unincludeRelations']
        
        manual_search = False
        
        variables = {
            'page': data_variables["pageNumber"],
            'sort': [data_variables["sortBy"]],
        }
        
        for key in data_variables:
            if key == "pageNumber" or key == "sortBy" or key == "studio":
                continue
            elif isinstance(data_variables[key], int):
                variables[key] = data_variables[key]
            elif isinstance(data_variables[key], str) and data_variables[key] != "":
                variables[key] = data_variables[key]
            elif key in manual_searchs and len(data_variables[key]) > 0:
                manual_search = True
            elif isinstance(data_variables[key], list) and len(data_variables[key]) > 0:
                variables[key] = data_variables[key]

        url = 'https://graphql.anilist.co'
        print(variables)
        
        
        media_list = []

        if manual_search:
            flag = True
            while flag:
                response = requests.post(url,
                 json={
                     'query': self.media_normal_search,
                     'variables': variables
                 })
                
                if response.status_code == 200:
                    # Parse the response JSON data
                    data = response.json()

                    print(len(data['data']['Page']['media']),
                          variables['page'])

                    print()
                    print(data_variables['includeRelations'])
                    print(data_variables['unincludeRelations'])

                    temp_media_list = data['data']['Page']['media']

                    if data_variables['includeRelations'] != []:
                        temp_media_list = self.must_include_relations(
                            temp_media_list,
                            data_variables['includeRelations'])

                    if data_variables['unincludeRelations'] != []:
                        temp_media_list = self.must_not_include_relations(
                            temp_media_list,
                            data_variables['unincludeRelations'])
                        
                    if 'distrabutionStatusGreaterThan' in data_variables and data_variables['distrabutionStatusGreaterThan'] != {}:
                        temp_media_list = self.stat_status_greater_than(
                            temp_media_list,
                            data_variables['distrabutionStatusGreaterThan'])
                        
                    if 'distrabutionStatusLesserThan' in data_variables and data_variables['distrabutionStatusLesserThan'] != {}:
                        temp_media_list = self.stat_status_lesser_than(
                            temp_media_list,
                            data_variables['distrabutionStatusLesserThan'])

                    media_list += temp_media_list

                    if len(media_list) >= 45 or len(
                            data['data']['Page']
                        ['media']) == 0:
                        flag = False
                    else:
                        variables['page'] += 1

                else:
                    print("oops")
                    print(response.json())
                    flag = False

        else:
            response = requests.post(url,
                                     json={
                                         'query': self.media_normal_search,
                                         'variables': variables
                                     })

            if response.status_code == 200:
                # Parse the response JSON data
                data = response.json()

                media_list = data.get('data', {}).get('Page',
                                                      {}).get('media', [])

            else:
                print("oops")
                print(response.json())
            

        return media_list, variables['page']


    def loop_for_manual_seaches(self, data_variables, animes):
        for key in data_variables:
            #4
            if key == "pageNumber" or key == "search" or key == "sortBy" or key == "studio":
                continue
            #5
            if animes == []:
                break
            elif isinstance(data_variables[key], int):
                #6
                if 'year' in key:
                    #7
                    if 'lesser' in key:
                        animes = self.must_be_lesser_than_year(animes, data_variables[key])
                    #8
                    else:
                        animes = self.must_be_greater_than_year(animes, data_variables[key])
                #9
                elif 'lesser' in key:
                    animes = self.must_be_lesser_than(animes, data_variables[key], key[:-8])
                #10
                else:
                    animes = self.must_be_greater_than(animes, data_variables[key], key[:-8])

            #11
            elif isinstance(data_variables[key], str) and data_variables[key] != "":
                animes = self.must_include_single(animes, data_variables[key], key)
            #12
            elif isinstance(data_variables[key], list) and len(data_variables[key]) > 0:
                #13
                if 'Relations' in key:
                    #14
                    if 'un' in key:
                        animes = self.must_not_include_relations(animes, data_variables[key])
                    #15
                    else:
                        animes = self.must_include_relations(animes, data_variables[key])
                #16
                else:
                    #17
                    if "not" in key:
                        animes = self.must_not_include_list(animes, data_variables[key], key)
                    #18
                    else:
                        animes = self.must_include_list(animes, data_variables[key], key)
            #19
            elif isinstance(data_variables[key], dict) and len(data_variables[key]) > 0:
                #20
                if "distrabutionStatus" in key:
                    #21
                    if "Greater" in key:
                        animes = self.stat_status_greater_than(animes, data_variables[key])
                    #22
                    else:
                        animes = self.stat_status_lesser_than(animes, data_variables[key])

        animes = self.remove_duplicates(animes)
        return animes


    def get_all_studio_anime(self, data_variables):

        variables = {
            'page': 1,
            'perPage': 50,
            'isAdult': False,
            'sort': [data_variables["sortBy"]],
            'animePage': data_variables["pageNumber"],
            'studioName': data_variables['studio']
        }

        media_list = []
        flag = True
        #1
        while flag:
            print(variables)
            url = 'https://graphql.anilist.co'

            response = requests.post(url,
                                     json={
                                         'query': self.media_studio_search,
                                         'variables': variables
                                     })
            #2
            if response.status_code == 200:
                data = response.json()
                media_list = data['data']['Page']['studios'][0]['media'][
                    'nodes']

                media_list += self.loop_for_manual_seaches(data_variables, media_list)

                print(len(media_list))
                #23
                if len(media_list) >= 45 or data['data']['Page']['studios'][0][
                        'media']['nodes'] == []:
                    flag = False
                #24
                else:
                    variables['animePage'] += 1

            #25
            else:
                flag = False
                print("oops")
                print(response.json())

        return media_list, data_variables["pageNumber"]

    def must_include_list(self, animes, must_include, catagory):
        for must_include_index in range(0, len(must_include)):
            anime_index = 0
            while anime_index < len(animes):
                if must_include[must_include_index] not in animes[anime_index][
                        catagory]:
                    animes.pop(anime_index)
                    print('anime removed')
                else:
                    anime_index += 1

        return animes

    def must_not_include_list(self, animes, must_include, catagory):
        for must_include_index in range(0, len(must_include)):
            anime_index = 0
            while anime_index < len(animes):
                if must_include[must_include_index] in animes[anime_index][
                        catagory]:
                    animes.pop(anime_index)
                    print('anime removed')
                else:
                    anime_index += 1

        return animes

    def must_include_single(self, animes, must_include, catagory):
        if must_include != "":
            anime_index = 0
            while anime_index < len(animes):
                if must_include != animes[anime_index][catagory]:
                    print(animes[anime_index]['season'], must_include)
                    animes.pop(anime_index)
                    print('anime removed')
                else:
                    anime_index += 1
        return animes

    def must_not_include_single(self, animes, must_include, catagory):
        if must_include != "":
            anime_index = 0
            while anime_index < len(animes):
                if must_include == animes[anime_index][catagory]:
                    print(animes[anime_index]['season'], must_include)
                    animes.pop(anime_index)
                    print('anime removed')
                else:
                    anime_index += 1
        return animes

    def must_include_relations(self, animes, relations):
        for relation_index in range(0, len(relations)):
            anime_index = 0
            while anime_index < len(animes):
                for relation in animes[anime_index]['relations']['edges']:
                    if relations[relation_index] == relation['relationType']:
                        anime_index += 1
                        break
                else:
                    animes.pop(anime_index)

        return animes

    def must_not_include_relations(self, animes, relations):
        for relation_index in range(0, len(relations)):
            anime_index = 0
            while anime_index < len(animes):
                for relation in animes[anime_index]['relations']['edges']:
                    if relations[relation_index] == relation['relationType']:
                        animes.pop(anime_index)
                        print('anime removed')
                        break
                else:
                    anime_index += 1
    
        return animes

    def must_be_greater_than(self, animes, min_num, option):
        anime_index = 0
        while anime_index < len(animes):

            if animes[anime_index][option] is None:
                current_num = 0
            else:
                current_num = animes[anime_index][option]

            if current_num <= min_num:
                animes.pop(anime_index)
            else:
                anime_index += 1

        return animes

    def must_be_lesser_than(self, animes, min_num, option):
        anime_index = 0
        while anime_index < len(animes):

            if animes[anime_index][option] is None:
                current_num = 0
            else:
                current_num = animes[anime_index][option]

            if current_num >= min_num:
                animes.pop(anime_index)
            else:
                anime_index += 1

        return animes

    def must_be_greater_than_year(self, animes, year):
        anime_index = 0
        while anime_index < len(animes):
            if animes[anime_index]["startDate"]['year'] is None:
                current_num = 0
            else:
                current_num = animes[anime_index]["startDate"]['year']

            print(current_num, year, current_num <= year)

            if current_num <= year:
                animes.pop(anime_index)
            else:
                anime_index += 1

        return animes

    def must_be_lesser_than_year(self, animes, year):
        anime_index = 0
        while anime_index < len(animes):
            if animes[anime_index]["startDate"]['year'] is None:
                current_num = 0
            else:
                current_num = animes[anime_index]["startDate"]['year']

            if current_num >= year:
                animes.pop(anime_index)
            else:
                anime_index += 1

        return animes

    def stat_status_greater_than(self, animes, statuses):
        anime_index = 0
        while anime_index < len(animes):
            for stat_index in range(
                    0,
                    len(animes[anime_index]['stats']['statusDistribution'])):
                if animes[anime_index]['stats']['statusDistribution'][
                        stat_index]['status'] in statuses:
                    if animes[anime_index]['stats']['statusDistribution'][
                            stat_index]['amount'] <= statuses[
                                animes[anime_index]['stats']
                                ['statusDistribution'][stat_index]['status']]:
                        animes.pop(anime_index)
                        break
            else:
                anime_index += 1

        return animes

    def stat_status_lesser_than(self, animes, statuses):
        anime_index = 0
        while anime_index < len(animes):
            #print(anime_index, "<", len(animes), "=", anime_index < len(animes))
            for stat_index in range(
                    0,
                    len(animes[anime_index]['stats']['statusDistribution'])):
                if animes[anime_index]['stats']['statusDistribution'][
                        stat_index]['status'] in statuses:
                    print(
                        animes[anime_index]['stats']['statusDistribution']
                        [stat_index]['amount'], ">=",
                        statuses[animes[anime_index]['stats']
                                 ['statusDistribution'][stat_index]['status']],
                        "=", animes[anime_index]['stats']['statusDistribution']
                        [stat_index]['amount'] >=
                        statuses[animes[anime_index]['stats']
                                 ['statusDistribution'][stat_index]['status']])

                    if animes[anime_index]['stats']['statusDistribution'][
                            stat_index]['amount'] >= statuses[
                                animes[anime_index]['stats']
                                ['statusDistribution'][stat_index]['status']]:
                        animes.pop(anime_index)
                        break
            else:
                anime_index += 1

        return animes

    def remove_duplicates(self, animes):
        index = 0
        while index < len(animes):
            if animes.count(animes[index]) > 1:
                animes.remove(animes[index])
                index -= 1
            index += 1

        return animes

    def sort_anime(self, sortBy, animes):
        for index in range(1, len(animes)):
            if animes[index - 1][sortBy] < animes[index][sortBy]:
                subtract_by = 1
                flag = True
                while flag:
                    if (index - subtract_by
                            == -1) or (animes[index - subtract_by][sortBy] >
                                       animes[index][sortBy]):
                        animes.insert(index - subtract_by + 1, animes[index])
                        animes.pop(index + 1)
                        flag = False
                    else:
                        subtract_by += 1

        return animes

    def get_staff(self, data_variables):
        variables = {
            'page': data_variables["pageNumber"],
            'perPage': 50,
            'isAdult': False,
            'sort': [data_variables["sortBy"]],
        }

        staff_list = []

        flag = True

        while flag:
            url = 'https://graphql.anilist.co'

            response = requests.post(url,
                                     json={
                                         'query': self.staff_query,
                                         'variables': variables
                                     })

            if response.status_code == 200:
                # Parse the response JSON data
                data = response.json()

                temp_staff_list = data['data']['Page']['staff']

                if data_variables['favouritesGreater'] != '':
                    temp_staff_list = self.must_be_greater_than(
                        temp_staff_list,
                        int(data_variables['favouritesGreater']), "favourites")

                if data_variables['favouritesLesser'] != '':
                    temp_staff_list = self.must_be_lesser_than(
                        temp_staff_list,
                        int(data_variables['favouritesLesser']), "favourites")

                staff_list += temp_staff_list

                if len(staff_list) > 49:
                    flag = False
                else:
                    variables['page'] += 1

                print(variables)

            else:
                print("oops")
                print(response.json())
                flag = False

        return staff_list, variables

    def get_staff_anime(self, data_variables):

        variables = {
            'page': data_variables["pageNumber"],
            'isAdult': False,
            'staffID': data_variables["id"],
            'sort': [data_variables["sortBy"]],
        }

        media_list = []
        character_list = []
        flag = True
        name = ''

        counter = 0
        while flag:
            counter += 1
            #print(variables)
            url = 'https://graphql.anilist.co'

            response = requests.post(url,
                                     json={
                                         'query': self.staff_anime_query,
                                         'variables': variables
                                     })
            if response.status_code == 200:
                data = response.json()
                name = data['data']['Page']['staff'][0]['name']['full']
                print(data['data']['Page']['staff'][0]['staffMedia']['edges'])
                if len(media_list) > 45 or data['data']['Page']['staff'][0][
                        'staffMedia']['edges'] == []:
                    flag = False
                else:
                    media_list += data['data']['Page']['staff'][0][
                        'staffMedia']['edges']
                    variables['page'] += 1

            else:
                flag = False
                print("oops")
                print(response.json())

            if counter == 1:
                first_data = data

        if data_variables["season"] != "":
            media_list = self.must_include_single(media_list,
                                                  data_variables["season"],
                                                  "season")

        if data_variables["yearGreater"] != "":
            media_list = self.must_be_greater_than_year(
                media_list, int(data_variables["yearGreater"]))

        if data_variables["yearLesser"] != "":
            media_list = self.must_be_lesser_than_year(
                media_list, int(data_variables["yearLesser"]))

        if data_variables["formatOption"] != "":
            media_list = self.must_include_single(
                media_list, data_variables["formatOption"], "format")

        if data_variables["mediaSource"] != "":
            pass

        if data_variables["averageScoreNumGreater"] != "":
            media_list = self.must_be_greater_than(
                media_list, int(data_variables["averageScoreNumGreater"]),
                'averageScore')

        if data_variables["averageScoreNumLesser"] != "":
            media_list = self.must_be_lesser_than(
                media_list, int(data_variables["averageScoreNumLesser"]),
                'averageScore')

        if data_variables["popularityNumGreater"] != "":
            media_list = self.must_be_greater_than(
                media_list, int(data_variables["popularityNumGreater"]),
                'popularity')

        if data_variables["popularityNumLesser"] != "":
            media_list = self.must_be_lesser_than(
                media_list, int(data_variables["popularityNumLesser"]),
                'popularity')

        if data_variables["episodeCountGreater"] != "":
            media_list = self.must_be_greater_than(
                media_list, int(data_variables["episodeCountGreater"]),
                'episodes')

        if data_variables["episodeCountLesser"] != "":
            media_list = self.must_be_lesser_than(
                media_list, int(data_variables["episodeCountLesser"]),
                'episodes')
            
        if len(data_variables["searchGenresInclude"]) > 0:
            media_list = self.must_include_list(
                media_list, data_variables["searchGenresInclude"], "genres")

        if len(data_variables["searchGenresUninclude"]) > 0:
            media_list = self.must_not_include_list(
                media_list, data_variables["searchGenresUninclude"], "genres")

        #media_list = self.remove_duplicates(media_list)

        return media_list, data_variables["pageNumber"]

    def get_staff_characters(self, data_variables):

        variables = {
            'page': data_variables["pageNumber"],
            'isAdult': False,
            'staffID': data_variables["id"],
            'sort': [data_variables["sortBy"]],
        }

        media_list = []
        character_list = []
        flag = True
        name = ''

        counter = 0
        while flag:
            counter += 1
            #print(variables)
            url = 'https://graphql.anilist.co'

            response = requests.post(url,
                                     json={
                                         'query': self.staff_character_query,
                                         'variables': variables
                                     })
            if response.status_code == 200:
                data = response.json()
                if len(character_list) > 45 or data['data']['Page']['staff'][
                        0]['characters']['edges'] == []:
                    flag = False
                else:
                    character_list += data['data']['Page']['staff'][0][
                        'characters']['edges']
                    variables['page'] += 1

            else:
                flag = False
                print("oops")
                print(response.json())

            if counter == 1:
                first_data = data

        #media_list = self.remove_duplicates(media_list)

        return character_list, data_variables["pageNumber"], first_data


get_anime = QueryAPI()


@app.route('/')
def index():
    """url = "https://graphql.anilist.co"
    query = '''
        query {
            SiteStatistics {
                users {
                    nodes {
                        date
                        count
                    }
                }
            }
        }
    '''
    response = requests.post(url, json={'query': query})
    data = response.json()
    if response.status_code == 200:
        print("working")
    else:
        print("oops")
        print(data)
    print(data)"""
    return redirect('/anime')


@app.route('/anime')
def anime():
    url = "https://graphql.anilist.co"
    query = '''
        query {
            GenreCollection,
            MediaTagCollection {
                id
                name
                description
                category
                rank
                isGeneralSpoiler
                isMediaSpoiler
                isAdult
                userId
          }
        }
    '''
    response = requests.post(url, json={'query': query})
    data = response.json()
    if response.status_code == 200:
        print("working")
    else:
        print("oops")
        print(data)

    session['all_genres'] = data['data']['GenreCollection']

    return render_template('anilist.html', genres=session['all_genres'])


@app.route('/search_anime', methods=["POST"])
def search_anime():
    data_variables = request.get_json()

    data_variables["genre_in"] = json.loads(
        data_variables["genre_in"])
    data_variables["genre_not_in"] = json.loads(
        data_variables["genre_not_in"])
    data_variables["includeRelations"] = json.loads(
        data_variables["includeRelations"])
    data_variables["unincludeRelations"] = json.loads(
        data_variables["unincludeRelations"])
    if "distrabutionStatusGreaterThan" in data_variables:
        data_variables["distrabutionStatusGreaterThan"] = json.loads(
            data_variables["distrabutionStatusGreaterThan"])
    if "distrabutionStatusLesserThan" in data_variables:
        data_variables["distrabutionStatusLesserThan"] = json.loads(
            data_variables["distrabutionStatusLesserThan"])

    for x in data_variables:
        print(x, data_variables[x])

    pageNumber = 0

    print(data_variables['studio'])
    if data_variables['studio'] == "":
        media_list, pageNumber = get_anime.get_anime(data_variables)

    else:

        media_list, pageNumber = get_anime.get_all_studio_anime(data_variables)

    return {'media_list': media_list, 'page': pageNumber}


@app.route('/anime_info/<int:id>')
def anime_info(id):
    url = "https://graphql.anilist.co"
    query = '''
    query (
        $id: Int,
        $page: Int, 
        $perPage: Int, 
    ) {
        Page (page: $page, perPage: $perPage) {
            pageInfo {
                total
                currentPage
                lastPage
                hasNextPage
                perPage
            }
            media (
                id: $id, 
            ) {
                id
                description (
                    asHtml: true
                )
                popularity
                averageScore
                trending
                favourites
                episodes
                duration
                genres
                season
                startDate {
                    year
                    month
                    day
                }
                endDate {
                    year
                    month
                    day
                }
                format
                bannerImage
                title {
                    romaji
                    english
                }
                studios {
                    edges {
                        isMain
                        node {
                            name
                        }
                    }
                }
                relations {
                    edges {
                        node {
                            id
                            title {
                                romaji
                                english
                            }
                            coverImage {
                                extraLarge
                                large
                                medium
                                color
                            }
                            siteUrl
                        }
                        relationType (version: 2)
                    }
                }
                title {
                    romaji
                    english
                }
                coverImage {
                    extraLarge
                    large
                    medium
                    color
                }
                siteUrl

            }
        }
    }
    '''
    variables = {
        'id': id,
        'page': 1,
        'perPage': 50,
    }

    response = requests.post(url,
                             json={
                                 'query': query,
                                 'variables': variables
                             })
    data = response.json()
    if response.status_code == 200:
        print("working")
    else:
        print("oops")
        print(data)

    data = data.get('data', {}).get('Page', {}).get('media', [])[0]

    return render_template('anime_info.html', data=data)


@app.route('/characters')
def characters():

    return render_template('characters.html')


@app.route('/staff')
def staff():
    return render_template('staff.html')


@app.route('/staff_info/<int:id>')
def staff_info(id):
    url = "https://graphql.anilist.co"
    query = '''
        query {
            GenreCollection,
            MediaTagCollection {
                id
                name
                description
                category
                rank
                isGeneralSpoiler
                isMediaSpoiler
                isAdult
                userId
          }
        }
    '''
    response = requests.post(url, json={'query': query})
    data = response.json()
    if response.status_code == 200:
        print("working")
    else:
        print("oops")
        print(data)

    all_genres = data['data']['GenreCollection']

    return render_template('staff_info.html', genres=all_genres, id=id)


@app.route('/search_staff', methods=["POST"])
def search_staff():
    data_variables = request.get_json()

    staff_list, variables = get_anime.get_staff(data_variables)

    return {'staff_list': staff_list, 'page': variables['page']}


@app.route('/search_staff_anime', methods=["POST"])
def search_staff_anime():
    data_variables = request.get_json()

    data_variables["searchGenresInclude"] = json.loads(
        data_variables["searchGenresInclude"])
    data_variables["searchGenresUninclude"] = json.loads(
        data_variables["searchGenresUninclude"])
    data_variables["includeRelations"] = json.loads(
        data_variables["includeRelations"])
    data_variables["unincludeRelations"] = json.loads(
        data_variables["unincludeRelations"])

    media_list, page = get_anime.get_staff_anime(data_variables)

    print("returing staff anime")
    return {
        'media_list': media_list,
        'page': page,
    }


@app.route('/search_staff_characters', methods=["POST"])
def search_staff_characters():
    data_variables = request.get_json()

    media_list, character_list, data = get_anime.get_staff_characters(
        data_variables)

    print("returing staff anime")
    return {
        'full data': data,
        'media_list': media_list,
        'page': 1,
        'character_list': character_list
    }


@app.route('/search_staff_manga', methods=["POST"])
def search_staff_manga():
    data_variables = request.get_json()

    media_list, character_list, data = get_anime.get_staff_characters(
        data_variables)

    print("returing staff anime")
    return {
        'full data': data,
        'media_list': media_list,
        'page': 1,
        'character_list': character_list
    }


@app.route('/search_character', methods=["POST"])
def search_character():
    data = request.get_json()

    for x in data:
        print(x, data[x])

    query = '''
    query (
        $page: Int,
        $perPage: Int

    ) {
        Page (page: $page, perPage: $perPage) {
            pageInfo {
                total
                currentPage
                lastPage
                hasNextPage
                perPage
            }
            characters {
                name {
                    full
                }
                image {
                    large
                    medium
                }
            }
        }
        
    }
    '''

    variables = {}

    print(variables)

    url = 'https://graphql.anilist.co'

    response = requests.post(url,
                             json={
                                 'query': query,
                                 'variables': variables
                             })

    media_list = []

    if response.status_code == 200:
        # Parse the response JSON data
        data = response.json()
        print(data['data'])

        # Access the relevant information from the response
        media_list = data.get('data', {}).get('Page', {}).get('characters', [])
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        media_list = []

    return media_list


app.run(host='0.0.0.0', port=81)
