from youtubeSpotifyConverter import youtubeSpotifyConverter

# Replace with your actual keys
YOUTUBE_API_KEY = "AIzaSyAzfVSgkjlofOZEuf2ixMDL3zgX_9xjIxE"
SPOTIFY_CLIENT_ID = "753433e40cf344d7862c37448330c736"
SPOTIFY_CLIENT_SECRET = "d9e646a7d5a74a46b17abdd1bd9ecd6f"

# Instantiate a youtubeSpotifyConverter object
converter = youtubeSpotifyConverter(YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

# Example Spotify URL
spotify_url = "https://open.spotify.com/track/0qlbvWRpZBKtaNeB6v8pD5?si=0fe45a5eb4cb4dd9"  # Replace with actual Spotify track URL

# Call the C_fromLink method to get the YouTube Music URL
links_from_spotify = converter.C_fromLink(spotify_url)

# Print the results
print("Converted links from Spotify URL:")
print(links_from_spotify)

