#Nathan Morris
#This is a personal project, I am trying to use spotify API to do a few different things including:
#Give me new music recommendations based on a playlist
#Pretty much do spotify wrapped whenever I want to
#End goal is to make a functional website that I can either put ads on to to make a little bit of money, or as a project for my resume

#I didn't use much commenting in the code, as the names of each def are pretty clear

import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from prettytable import PrettyTable
import sys
import re

# Initialize Spotipy with OAuth
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='566c0743af384beab5f443bbd02e52d7', 
                                               client_secret='429d1782cbce41ffad72b969f09b3366',
                                               redirect_uri='http://localhost:8888/callback',
                                               scope='playlist-modify-private playlist-modify-public user-library-read user-top-read'))

def extract_playlist_id(playlist_link):
    regex = r'playlist\/([a-zA-Z0-9]+)'
    match = re.search(regex, playlist_link)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid Spotify playlist link format")

def get_all_user_tracks():
    try:
        all_tracks = set()
        
        # Fetch user playlists
        playlists = sp.current_user_playlists()['items']
        for playlist in playlists:
            playlist_id = playlist['id']
            results = sp.playlist_tracks(playlist_id)
            tracks = results['items']
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])
            
            for track in tracks:
                if track['track'] is not None:
                    all_tracks.add(track['track']['id'])
        
        # Fetch liked songs
        results = sp.current_user_saved_tracks()
        for item in results['items']:
            track = item['track']
            if track is not None:
                all_tracks.add(track['id'])
        
        return all_tracks
    
    except Exception as e:
        print(f"Error fetching user tracks: {e}")
        sys.exit(1)

#gets info on each track/song
def get_audio_features(track_ids):
    features = sp.audio_features(track_ids)
    return features

def get_recommendations(seed_tracks, num_recommendations, user_track_ids):
    recommended_tracks = []
    while len(recommended_tracks) < num_recommendations + 1:
        # Limit the number of recommendations to 100 per request(limitation via spotify)
        limit = min(num_recommendations + 1 - len(recommended_tracks), 100)
        recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=limit)
        
        for rec_track in recommendations['tracks']:
            if rec_track['id'] not in user_track_ids and rec_track['id'] not in [track['id'] for track in recommended_tracks]:
                recommended_tracks.append(rec_track)
                if len(recommended_tracks) == num_recommendations + 1:
                    break
    
    return recommended_tracks[:num_recommendations]  # Return only the specified number of recommendations

def create_playlist(name):
    try:
        playlist = sp.user_playlist_create(sp.current_user()['id'], name, public=False)
        return playlist['id']
    except Exception as e:
        print(f"Error creating playlist: {e}")
        sys.exit(1)

def add_tracks_to_playlist(playlist_id, track_ids):
    try:
        sp.user_playlist_add_tracks(sp.current_user()['id'], playlist_id, track_ids)
        print(f"Tracks added to playlist successfully!")
    except Exception as e:
        print(f"Error adding tracks to playlist: {e}")
        sys.exit(1)

def view_top_artists():
    top_artists = sp.current_user_top_artists(limit=50, time_range='long_term')['items']
    table = PrettyTable()
    table.field_names = ["Number", "Artist Name"]
    for i, artist in enumerate(top_artists, 1):
        table.add_row([i, artist['name']])
    print("Top Artists from the last 12 months:")
    table.align = "l"
    print(table)

def view_top_genres():
    top_artists = sp.current_user_top_artists(limit=50, time_range='long_term')['items']
    genres = {}
    for artist in top_artists:
        for genre in artist['genres']:
            if genre in genres:
                genres[genre] += 1
            else:
                genres[genre] = 1
    sorted_genres = sorted(genres.items(), key=lambda item: item[1], reverse=True)
    table = PrettyTable()
    table.field_names = ["Number", "Genre", "Count"]
    for i, (genre, count) in enumerate(sorted_genres, 1):
        table.add_row([i, genre, count])
    print("Top Genres from the last 12 months:")
    table.align = "l"
    print(table)

    #Aks user if they want to explore a genre(creates a new playlist with only that genre)
    explore = input("Would you like to explore a genre (Y/N)? ").strip().lower()
    if explore == 'y':
        genre_number = int(input("Enter the number of the genre you want to explore: "))
        if 1 <= genre_number <= len(sorted_genres):
            selected_genre = sorted_genres[genre_number - 1][0]
            print(f"Exploring genre: {selected_genre}")
            create_genre_playlist(selected_genre)
        else:
            print("Invalid genre number.")

def view_top_songs():
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')['items']
    table = PrettyTable()
    table.field_names = ["Number", "Title", "Artists"]
    for i, track in enumerate(top_tracks, 1):
        track_name = track['name']
        track_artists = ', '.join([artist['name'] for artist in track['artists']])
        table.add_row([i, track_name, track_artists])
    print("Top Songs from the last 12 months:")
    table.align = "l"
    print(table)

def create_recommendation_playlist_from_top_tracks():
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')['items']
    track_ids = [track['id'] for track in top_tracks]
    user_track_ids = get_all_user_tracks()

    #only able to use 5 seed tracks(spotify limitation)
    seed_tracks = random.sample(track_ids, 5)  # Use 5 random tracks from the top tracks as seed tracks
    num_recommendations = int(input("Enter the number of recommendations you want: "))
    recommendations = get_recommendations(seed_tracks, num_recommendations, user_track_ids)

    RecTable = PrettyTable()
    RecTable.field_names = ["Title", "Artists"]
    rec_track_ids = []
    for rec_track in recommendations:
        rec_track_name = rec_track.get('name', 'Unknown')
        rec_track_artists = ', '.join([artist['name'] for artist in rec_track.get('artists', [{'name': 'Unknown'}])])
        RecTable.add_row([rec_track_name, rec_track_artists])
        rec_track_ids.append(rec_track['id'])

    print("Recommended Songs:")
    RecTable.align = "l"
    print(RecTable)

    # Create a new playlist and add recommended tracks to it
    playlist_name = input("Enter the name of the new playlist: ")
    new_playlist_id = create_playlist(playlist_name)
    add_tracks_to_playlist(new_playlist_id, rec_track_ids)

def create_recommendation_playlist_from_playlist():
    playlist_link = input("Enter the Spotify playlist link: ").strip()
    playlist_id = extract_playlist_id(playlist_link)
    user_track_ids = get_all_user_tracks()
    tracks = sp.playlist_tracks(playlist_id)['items']
    
    track_ids = []
    for track in tracks:
        if track['track'] is not None:
            track_ids.append(track['track']['id'])

    table = PrettyTable()
    table.field_names = ["Title", "Artists"]

    for track_id in track_ids:
        track = sp.track(track_id)
        track_name = track['name']
        track_artists = ', '.join([artist['name'] for artist in track['artists']])
        table.add_row([track_name, track_artists])
    
    print("Tracks fetched from playlist:")
    table.align = "l"
    print(table)

    seed_tracks = random.sample(track_ids, 5)  # Use 5 random tracks from the specified playlist as seed tracks

    num_recommendations = int(input("Enter the number of recommendations you want: "))
    recommendations = get_recommendations(seed_tracks, num_recommendations, user_track_ids)

    RecTable = PrettyTable()
    RecTable.field_names = ["Title", "Artists"]
    rec_track_ids = []
    for rec_track in recommendations:
        rec_track_name = rec_track.get('name', 'Unknown')
        rec_track_artists = ', '.join([artist['name'] for artist in rec_track.get('artists', [{'name': 'Unknown'}])])
        RecTable.add_row([rec_track_name, rec_track_artists])
        rec_track_ids.append(rec_track['id'])

    print("Recommended Songs:")
    RecTable.align = "l"
    print(RecTable)

    playlist_name = input("Enter the name of the new playlist: ")
    new_playlist_id = create_playlist(playlist_name)
    add_tracks_to_playlist(new_playlist_id, rec_track_ids)

def create_genre_playlist(genre):
    try:
        # Search for tracks of the specified genre
        results = sp.search(q=f'genre:"{genre}"', type='track', limit=50)
        genre_tracks = [track['id'] for track in results['tracks']['items']]
        
        if not genre_tracks:
            print(f"No tracks found for genre: {genre}")
            return
        
        # Create a new playlist with the genre name
        playlist_name = genre.capitalize() + " Playlist"
        new_playlist_id = create_playlist(playlist_name)
        add_tracks_to_playlist(new_playlist_id, genre_tracks)

        print(f"Created playlist '{playlist_name}' with {len(genre_tracks)} tracks of genre '{genre}'.")

    except Exception as e:
        print(f"Error creating genre playlist: {e}")
        sys.exit(1)

def main():
    #a loop with the menu, 6 exits the loop
    while True:
        print("Please select an option from the list below:")
        menu = PrettyTable()
        menu.field_names = ["Option", "Description"]
        options = [
            "Create recommendation playlist from one of your playlists",
            "View top artists from the last 12 months",
            "View top genres of the last 12 months",
            "View top songs of the last 12 months",
            "Create recommendation playlist from your top songs",
            "Exit"
        ] 
        for i, option in enumerate(options, 1):
            menu.add_row([i, option])
        menu.align = "l"
        print(menu)
    
        choice = int(input("Enter the option number: "))

        if choice == 1:
            create_recommendation_playlist_from_playlist()
        elif choice == 2:
            view_top_artists()
        elif choice == 3:
            view_top_genres()
        elif choice == 4:
            view_top_songs()
        elif choice == 5:
            create_recommendation_playlist_from_top_tracks()
        elif choice == 6:
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")

if __name__ == "__main__":
    main()
