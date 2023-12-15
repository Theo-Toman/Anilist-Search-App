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
"""login_manager = LoginManager()
login_manager.init_app(app)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



db = SQLAlchemy(app)


app.app_context().push()
with app.app_context():
    db.create_all()"""


class GetAnime:

    def __init__(self):
        self.media_normal_search = '''
            query (
                $id: Int,
                $page: Int,
                $perPage: Int,
                $search: String,
                $popularity_lesser: Int,
                $popularity_greater: Int,
                $averageScore_lesser: Int,
                $averageScore_greater: Int,
                $sort: [MediaSort],
                $isAdult: Boolean,
                $format: MediaFormat, 
                $genre_in: [String],
                $genre_not_in: [String],
                $source: MediaSource,
                $season: MediaSeason,
                $seasonYear: Int,
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
                        search: $search, 
                        popularity_lesser: $popularity_lesser, 
                        popularity_greater: $popularity_greater, 
                        averageScore_lesser: $averageScore_lesser, 
                        averageScore_greater: $averageScore_greater, 
                        type: ANIME, 
                        sort: $sort, 
                        isAdult: $isAdult, 
                        format: $format, 
                        genre_in: $genre_in, 
                        genre_not_in: $genre_not_in,
                        source: $source,
                        season: $season,
                        seasonYear: $seasonYear
    
                    ) {
                        id
                        popularity
                        averageScore
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
            ) {
                Page (page: $page, perPage: $perPage) {
                    pageInfo {
                        total
                        currentPage
                        lastPage
                        hasNextPage
                        perPage
                    }
                    studios (search: $studioName) {
                        media (
                            page: $animePage, perPage: $perPage
                        ) {
                                nodes {
    
                                        id
                                        popularity
                                        averageScore
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
    
                                }
    
                        }
    
                    }
    
                }
            }
            '''

    def get_anime(self, data_variables):
        variables = {
            'page': data_variables["pageNumber"],
            'perPage': 50,
            'isAdult': False,
            'sort': [data_variables["sortBy"]],
        }

        if data_variables["search"] != "":
            variables["search"] = data_variables["search"]

        if data_variables["popOption"] != "" and data_variables["popNum"] != "":
            variables[data_variables["popOption"]] = data_variables["popNum"]

        if data_variables["formatOption"] != "":
            variables['format'] = data_variables["formatOption"]

        if data_variables["mediaSource"] != "":
            variables['source'] = data_variables["mediaSource"]

        if data_variables["startingYear"] != "":
            variables['seasonYear'] = data_variables["startingYear"]

        if data_variables["season"] != "":
            variables['season'] = data_variables["season"]

        if data_variables["averageScoreOption"] != "" and data_variables[
                "averageScoreNum"] != "":
            variables[data_variables["averageScoreOption"]] = data_variables[
                "averageScoreNum"]

        if len(data_variables["searchGenresInclude"]) > 0:
            variables['genre_in'] = data_variables["searchGenresInclude"]

        if len(data_variables["searchGenresUninclude"]) > 0:
            variables['genre_not_in'] = data_variables["searchGenresUninclude"]

        media_list = []
        if data_variables['includeRelations'] == [] and data_variables[
                'unincludeRelations'] == []:
            url = 'https://graphql.anilist.co'

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
        else:
            flag = True
            while flag:
                url = 'https://graphql.anilist.co'
                print(variables)
                response = requests.post(url,
                                         json={
                                             'query': self.media_normal_search,
                                             'variables': variables
                                         })

                if response.status_code == 200:
                    # Parse the response JSON data
                    data = response.json()

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

                    media_list += temp_media_list

                    if len(media_list) >= 50 or (data['data']['Page']['media']) == 0 or variables['page'] > 50:
                        flag = False
                    else:
                        variables['page'] += 1

                else:
                    print("oops")
                    print(response.json())
                    flag = False

        return media_list, variables['page']

    def get_all_studio_anime(self, studio, variables):
        media_list = []
        flag = True
        while flag:
            print(variables)
            url = 'https://graphql.anilist.co'

            response = requests.post(url,
                                     json={
                                         'query': self.media_studio_search,
                                         'variables': variables
                                     })
            if response.status_code == 200:
                data = response.json()
                if data['data']['Page']['studios'][0]['media']['nodes'] == []:
                    flag = False
                else:
                    media_list += data['data']['Page']['studios'][0]['media'][
                        'nodes']
                    variables['animePage'] += 1
            else:
                flag = False
                print("oops")
                print(response.json())
        return media_list

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


get_anime = GetAnime()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/anilist')
def anilist():
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

    for x in data_variables:
        print(x, data_variables[x])
    print(data_variables)

    data_variables["searchGenresInclude"] = json.loads(
        data_variables["searchGenresInclude"])
    data_variables["searchGenresUninclude"] = json.loads(
        data_variables["searchGenresUninclude"])
    data_variables["includeRelations"] = json.loads(
        data_variables["includeRelations"])
    data_variables["unincludeRelations"] = json.loads(
        data_variables["unincludeRelations"])

    variables = {
        'page': data_variables["pageNumber"],
        'perPage': 50,
        'isAdult': False,
        'sort': [data_variables["sortBy"]],
        'animePage': 1,
    }

    print(data_variables['studio'])
    if data_variables['studio'] == "":
        media_list, variables['page'] = get_anime.get_anime(data_variables)

    else:
        query = get_anime.media_studio_search
        variables['studioName'] = data_variables["studio"]

        media_list = get_anime.get_all_studio_anime(data_variables['studio'],
                                                    variables)

        if data_variables["season"] != "":
            media_list = get_anime.must_include_single(
                media_list, data_variables["season"], "season")

        if data_variables["startingYear"] != None:
            media_list = get_anime.must_include_single(
                media_list, data_variables["startingYear"], "seasonYear")

        if data_variables["formatOption"] != "":
            media_list = get_anime.must_include_single(
                media_list, data_variables["formatOption"], "format")

        if data_variables["mediaSource"] != "":
            pass

        if data_variables["averageScoreOption"] != "":
            pass

        sortBy = data_variables['sortBy'].split("_")[0].lower()

        if sortBy == "score":
            sortBy = "averageScore"

        if len(data_variables["searchGenres"]) > 0:
            media_list = get_anime.must_include_list(
                media_list, data_variables["searchGenresInclude"], "genres")

        media_list = get_anime.sort_anime(sortBy, media_list)

    return {'media_list': media_list, 'page': variables['page']}


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
                popularity
                averageScore
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

    #print(data)

    print(data['title']['romaji'])
    print(data['coverImage']['medium'])
    print(data['relations']['edges'])

    return render_template('anime_info.html',
                           title=data['title']['romaji'],
                           image=data['coverImage']['medium'],
                           relations=data['relations']['edges'])


@app.route('/characters')
def characters():

    return render_template('characters.html')


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
