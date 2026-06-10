# supabase_client.py
# Handles all communication with the Supabase REST API (POST and GET requests)
import urequests  # MicroPython HTTP library for making web requests
import ujson      # MicroPython JSON library for encoding/decoding data
from config import SUPABASE_URL, SUPABASE_KEY, TABLE_SENSORS, TABLE_SETTINGS

def post_reading(light_level, led_status):
    # Base URL for the table
    url = "{}/rest/v1/{}".format(SUPABASE_URL, TABLE_SENSORS)

    # Headers required by Supabase REST API
    # "Prefer: return=minimal" tells Supabase not to send the whole row back, saving ESP32 memory
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
        "Prefer": "return=minimal" 
    }

    # Build the data dictionary
    payload = {
        "light_level": light_level,
        "led_status": led_status
    }

    try:
        # POST request to append a new row to the table
        response = urequests.post(url, headers=headers, data=ujson.dumps(payload))
        print("POST (Insert) status:", response.status_code) # 201 indicates a successful creation
        response.close() # Free memory immediately
            
    except Exception as e:
        print("Request error:", e)

# Previous attempt to do conditional POST/PATCH based on table emptiness
'''
def post_reading(light_level, led_status):
    # Base URL for the table
    url = "{}/rest/v1/{}".format(SUPABASE_URL, TABLE_SENSORS)

    # Base headers required by Supabase REST API
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY
    }

    # Build the data dictionary
    payload = {
        "light_level": light_level,
        "led_status": led_status
    }

    try:
        # 1. GET request to check if the table is empty
        # We limit the request to 1 row to save ESP32 memory
        get_url = url + "?select=*&limit=1"
        get_response = urequests.get(get_url, headers=headers)
        rows = ujson.loads(get_response.text)
        get_response.close() # Free memory immediately

        # Add the 'Prefer' header to our insert/update headers to save memory
        write_headers = headers.copy()
        write_headers["Prefer"] = "return=minimal"

        # 2. Check if table is empty and POST/PATCH accordingly
        if len(rows) == 0:
            # Table is empty: POST (Insert)
            response = urequests.post(url, headers=write_headers, data=ujson.dumps(payload))
            print("POST (Insert) status:", response.status_code) # 201 = success
            response.close()
            
        else:
            # Table is not empty: PATCH (Update)
            # We must specify WHICH row to update. We use the 'id' of the row we just fetched.
            row_id = rows[0].get("id")
            
            if row_id is not None:
                # Add the ID filter to the URL (e.g., ?id=eq.1)
                patch_url = url + "?id=eq.{}".format(row_id)
                response = urequests.patch(patch_url, headers=write_headers, data=ujson.dumps(payload))
                print("PATCH (Update) status:", response.status_code) # 204 or 200 = success
                response.close()
            else:
                print("Error: Row found, but no 'id' column exists to target the PATCH request.")

    except Exception as e:
        print("Request error:", e)
'''

'''

def get_readings(limit=1):
    # Fetches the most recent rows from the device settings table
    # ?select=* — return all columns
    # &order=created_at.desc — newest first
    # &limit=N — only return N rows
    # Query the settings table (used to retrieve device settings)
    url = "{}/rest/v1/{}?select=light_threshold,lcd_message&order=created_at.desc&limit={}".format(
        SUPABASE_URL, TABLE_SENSORS, limit
    )

    # GET requests only need the API key headers (no Content-Type needed)
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY
    }

    try:
        response = urequests.get(url, headers=headers)
        print("GET readings status:", response.status_code)  # 200 = success

        # If Supabase returns an error (400/4xx/5xx), attempt to parse and print
        # the JSON body which often contains `code`, `message`, `hint`, `details`.
        if response.status_code != 200:
            try:
                err = ujson.loads(response.text)
                print("GET error body:", err)
                for key in ("code", "message", "hint", "details"):
                    if key in err:
                        print("{}: {}".format(key, err[key]))
            except Exception:
                print("GET error response text:", response.text)
            response.close()
            return []

        data = ujson.loads(response.text)  # Parse the JSON response into a Python list
        response.close()
        return data  # Returns a list of dictionaries, one per row
    except Exception as e:
        print("GET readings error:", e)
        return []  # Return empty list so the main loop can continue safely
'''

def get_lcd_message():
    # Order by your primary key or timestamp descending, limit to 1
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_SETTINGS}?select=lcd_message&order=created_at.desc&limit=1"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = urequests.get(url, headers=headers)
        if response.status_code == 200:
            data = ujson.loads(response.text)
            if data and len(data) > 0:
                return data[0].get("lcd_message", "")
        else:
            print("Failed to fetch settings. Status:", response.status_code)
        return None
    except Exception as e:
        print("Error fetching LCD message:", e)
        return None
    finally:
        # Always close the connection to prevent memory leaks on the ESP32
        if 'response' in locals():
            response.close()


def get_light_threshold():
    # Order by your primary key or timestamp descending, limit to 1
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_SETTINGS}?select=light_threshold&order=created_at.desc&limit=1"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = urequests.get(url, headers=headers)
        if response.status_code == 200:
            data = ujson.loads(response.text)
            if data and len(data) > 0:
                return data[0].get("light_threshold", None)
        else:
            print("Failed to fetch settings. Status:", response.status_code)
        return None
    except Exception as e:
        print("Error fetching light threshold:", e)
        return None
    finally:
        # Always close the connection to prevent memory leaks on the ESP32
        if 'response' in locals():
            response.close()