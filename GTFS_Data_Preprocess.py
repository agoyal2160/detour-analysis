import requests, os, zipfile
import time, sqlite3
import pandas as pd

def extract_gtfs_data(repo_owner, repo_name, output_folder):

    latest_release_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    response = requests.get(latest_release_url)
    if response.status_code != 200:
        raise Exception("Failed to fetch the latest release.")

    release_info = response.json()
    assets = release_info.get('assets')
    if not assets:
        raise Exception("No assets found in the latest release.")
    
    for asset in assets:
        if asset.get('name') == "gtfs_public.zip":
            download_url = asset.get('browser_download_url')
            response = requests.get(download_url)

            with open(os.path.join(output_folder, "gtfs_public.zip"), "wb") as file:
                file.write(response.content)
            break

def preprocess_gtfs_files(gtfs_bus_folder):

    trips_file_path = os.path.join(gtfs_bus_folder, "trips.txt")
    stop_times_file_path = os.path.join(gtfs_bus_folder, "stop_times.txt")
    stops_file_path = os.path.join(gtfs_bus_folder, "stops.txt")

    df_trips = pd.read_csv(trips_file_path, sep=",")
    df_stop_times = pd.read_csv(stop_times_file_path, sep=",")
    df_stops = pd.read_csv(stops_file_path, sep=",")

    conn = sqlite3.connect(':memory:')
    df_trips.to_sql('trips', conn, index=False)
    df_stop_times.to_sql('stop_times', conn, index=False)
    df_stops.to_sql('stops', conn, index=False)

    query = """SELECT t.route_id, t.trip_id, t.trip_headsign, t.direction_id, t.shape_id, st.stop_id, st.stop_sequence, s.stop_name, s.stop_lat, s.stop_lon
    FROM trips as t INNER JOIN stop_times as st ON t.trip_id = st.trip_id INNER JOIN stops as s ON st.stop_id = s.stop_id
    GROUP BY t.route_id, t.trip_headsign, t.direction_id, t.shape_id, st.stop_id ORDER BY st.stop_sequence;"""

    trips_stop_times_stop_files_df = pd.read_sql_query(query, con=conn)
    conn.close()

    print(trips_stop_times_stop_files_df)
    return trips_stop_times_stop_files_df

if __name__ == "__main__":
    start_time = time.time()

    gtfs_github_repo_owner = 'septadev'
    gtfs_github_repo_name = 'GTFS'
    output_folder = "gtfs_data"
    gtfs_bus_data_folder = "gtfs_data/google_bus"
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(gtfs_bus_data_folder, exist_ok=True)

    extract_gtfs_data(gtfs_github_repo_owner, gtfs_github_repo_name, output_folder)

    gtfs_public_zip_path = os.path.join(output_folder, "gtfs_public.zip")
    
    with zipfile.ZipFile(gtfs_public_zip_path, "r") as zip_ref:
        zip_ref.extractall(output_folder)
    
    google_bus_zip_path = os.path.join(output_folder, "google_bus.zip")

    with zipfile.ZipFile(google_bus_zip_path, "r") as zip_ref:
        zip_ref.extractall(gtfs_bus_data_folder)

    preprocessed_trips_stop_times_stop_df = preprocess_gtfs_files(gtfs_bus_data_folder)

    preprocessed_trips_stop_times_stop_df.to_csv(os.path.join(gtfs_bus_data_folder, "preprocessed_trips_stop_times_stop.txt"), index=False, sep=',')

    print( f'Processed in ' + '{}'.format((time.time() - start_time)) + ' seconds' )


