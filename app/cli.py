from cassandra.cluster import Cluster
import time
import random
import threading
from datetime import datetime


# Setup Schema
def setup_schema(session):
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS cinema
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 2}
    """)
    session.set_keyspace('cinema')

    session.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            movie_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT
        )
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS showtimes (
            showtime_id TEXT PRIMARY KEY,
            movie_id TEXT,
            start_time TIMESTAMP,
            auditorium TEXT
        )
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            showtime_id TEXT,
            seat_number TEXT,
            user_id TEXT,
            reserved_at TIMESTAMP,
            PRIMARY KEY (showtime_id, seat_number)
        )
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS showtimes_by_movie (
            movie_id TEXT,
            showtime_id TEXT,
            start_time TIMESTAMP,
            auditorium TEXT,
            PRIMARY KEY (movie_id, showtime_id)
        )
    """)

# Node selection
def connect():
    nodes = ['cassandra-node1', 'cassandra-node2']
    print("Available Cassandra nodes:")
    for i, node in enumerate(nodes):
        print(f"{i + 1}. {node}")
    
    try:
        selected = int(input("Select a node to connect to (1-2): ").strip())
        if 1 <= selected <= len(nodes):
            node = nodes[selected - 1]
            print(f"\nConnecting to {node}...")
            cluster = Cluster([node])
            session = cluster.connect()
            setup_schema(session)
            return cluster, session
        else:
            print("Invalid selection. Exiting.")
            exit()
    except Exception as e:
        print("Connection failed:", e)
        exit()


# Seed data
def seed_data(session):
    movies = [
        ("Inception", "A dream within a dream."),
        ("The Matrix", "Reality is an illusion."),
        ("Interstellar", "A journey through space and time.")
    ]
    first_showtime_id = None

    for idx, (title, desc) in enumerate(movies):
        movie_id = f"movie_{idx}"
        session.execute("INSERT INTO movies (movie_id, title, description) VALUES (%s, %s, %s)", (movie_id, title, desc))

        for i in range(2):
            showtime_id = f"{movie_id}_showtime_{i}"
            start_time = datetime.utcnow()
            session.execute("INSERT INTO showtimes (showtime_id, movie_id, start_time, auditorium) VALUES (%s, %s, %s, %s)",
                            (showtime_id, movie_id, start_time, f"Room {i}"))
            session.execute("INSERT INTO showtimes_by_movie (movie_id, showtime_id, start_time, auditorium) VALUES (%s, %s, %s, %s)",
                            (movie_id, showtime_id, start_time, f"Room {i}"))
            if not first_showtime_id:
                first_showtime_id = showtime_id
    return first_showtime_id

# Regular Use Mode Functions
def select_movie(session):
    print("\nAvailable Movies:")
    rows = list(session.execute("SELECT movie_id, title FROM movies"))
    if not rows:
        print("No movies found.")
        return None

    for idx, row in enumerate(rows):
        print(f"{idx + 1}. {row.title}")
    try:
        choice = int(input("Select a movie: ")) - 1
        return rows[choice].movie_id
    except:
        print("Invalid choice.")
        return None

def select_showtime(session, movie_id):
    print(f"\nAvailable Showtimes for Movie ID {movie_id}:")
    rows = list(session.execute("SELECT showtime_id, start_time, auditorium FROM showtimes_by_movie WHERE movie_id = %s", (movie_id,)))
    if not rows:
        print("No showtimes.")
        return None

    for idx, row in enumerate(rows):
        print(f"{idx + 1}. {row.start_time} - {row.auditorium}")
    try:
        choice = int(input("Select a showtime: ")) - 1
        return rows[choice].showtime_id
    except:
        print("Invalid choice.")
        return None

def make_reservation(session, showtime_id, seat, user, log=False):
    try:
        query = "INSERT INTO reservations (showtime_id, seat_number, user_id, reserved_at) VALUES (%s, %s, %s, toTimestamp(now())) IF NOT EXISTS"
        result = session.execute(query, (showtime_id, seat, user))
        if result[0].applied:
            if log:
                print(f"Seat {seat} reservation successful.")
            return True
        else:
            if log:
                print(f"Seat {seat} already reserved.")
            return False
    except Exception as e:
        print("Error:", e)
        return False

def update_reservation(session, showtime_id, seat, new_user_id):
    print(f"Updating reservation for seat {seat} at showtime {showtime_id} to user {new_user_id}...")
    query = "UPDATE reservations SET user_id = %s, reserved_at = toTimestamp(now()) WHERE showtime_id = %s AND seat_number = %s"
    session.execute(query, (new_user_id, showtime_id, seat))
    print("Reservation updated.")

def list_reservations(session, showtime_id):
    print(f"\nReservations for showtime {showtime_id}:")
    rows = session.execute("SELECT seat_number, user_id, reserved_at FROM reservations WHERE showtime_id = %s", (showtime_id,))
    for row in rows:
        print(f"Seat: {row.seat_number} | User: {row.user_id} | At: {row.reserved_at}")

def who_reserved(session, showtime_id, seat):
    print(f"Checking who reserved seat {seat} for showtime {showtime_id}...")
    row = session.execute("SELECT user_id FROM reservations WHERE showtime_id = %s AND seat_number = %s", (showtime_id, seat)).one()
    if row:
        print(f"Seat {seat} reserved by {row.user_id}")
    else:
        print("Seat not reserved.")

# CLI Regular Mode
def regular_use_mode(session, current_showtime, user_id):
    movie_id = select_movie(session)
    if movie_id:
        showtime_id = select_showtime(session, movie_id)
        if showtime_id:
            current_showtime = showtime_id

    while True:
        print("\nCinema Reservation Menu\n")
        print("\n1. Reserve seat\n2. Change movie\n3. Update reservation\n4. View reservations\n5. Who reserved seat\n6. Back\n7. Exit")
        choice = input("Choice: ")
        if choice == "1":
            seat = input("Seat: ")
            make_reservation(session, current_showtime, seat, user_id, log=True)
        elif choice == "2":
            movie_id = select_movie(session)
            if movie_id:
                showtime_id = select_showtime(session, movie_id)
                if showtime_id:
                    current_showtime = showtime_id
        elif choice == "3":
            seat = input("Seat: ")
            new_user = input("New user_id: ")
            update_reservation(session, current_showtime, seat, new_user)
        elif choice == "4":
            list_reservations(session, current_showtime)
        elif choice == "5":
            seat = input("Seat: ")
            who_reserved(session, current_showtime, seat)
        elif choice == "6":
            return
        elif choice == "7":
            exit()
        else:
            print("Invalid choice. Please try again.")

# Stress Test Functions
def generate_seat():
    row = random.choice("ABCDEFGHIJKLM")
    num = random.randint(1, 50)
    return f"{row}{num}"


def stress_test_1(session, showtime_id="stress_test_1"):
    print("\nStress Test 1: Bulk Insert")
    for i in range(500):
        seat = generate_seat()
        make_reservation(session, showtime_id, seat, f"{user_id}_bulk{i}", log=True)
    print("Stress Test 1 complete")
    clear_reservations(session, showtime_id)


def stress_test_2(session, showtime_id="stress_test_2"):
    print("\nStress Test 2: Rapid-fire same seat")
    seat = "Z1"
    for _ in range(2):
        make_reservation(session, showtime_id, seat, user_id, log=True)
    print("Stress Test 2 complete")
    clear_reservations(session, showtime_id)


def stress_test_3(session, showtime_id="stress_test_3"):
    def client(name):
        for _ in range(25):
            seat = generate_seat()
            make_reservation(session, showtime_id, seat, f"{name}_{random.randint(1, 100)}", log=True)
            time.sleep(random.uniform(0.05, 0.1))

    print("\nStress Test 3: Multiple clients random")
    threads = [threading.Thread(target=client, args=(f"client_{i}",)) for i in range(3)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    print("Stress Test 3 complete")
    clear_reservations(session, showtime_id)


def stress_test_4(session, showtime_id="stress_test_4"):
    print("\nStress Test 4: Competing reservations")

    seat_ids = [f"A{i}" for i in range(1, 21)]
    summary = {1: 0, 2: 0}

    cluster1 = Cluster(['cassandra-node1'])
    session1 = cluster1.connect()
    session1.set_keyspace('cinema')

    cluster2 = Cluster(['cassandra-node2'])
    session2 = cluster2.connect()
    session2.set_keyspace('cinema')

    def reserve_all(session, client_id):
        user_id = f"user_{client_id}"
        for seat_id in seat_ids:
            time.sleep(random.uniform(0.01, 0.05)) 
            try:
                result = make_reservation(session, showtime_id, seat_id, user_id)
                if result:
                    summary[client_id] += 1
                    print(f"[Client {client_id}] Reserved {seat_id}")
                else:
                    print(f"[Client {client_id}] {seat_id} already taken")
            except Exception as e:
                print(f"[Client {client_id}] Error reserving {seat_id}: {e}")

    t1 = threading.Thread(target=reserve_all, args=(session1, 1))
    t2 = threading.Thread(target=reserve_all, args=(session2, 2))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print(f"Client 1: {summary[1]} reservations")
    print(f"Client 2: {summary[2]} reservations")

    cluster1.shutdown()
    cluster2.shutdown()
    clear_reservations(session, showtime_id)

def clear_reservations(session, showtime_id):
    print(f"\nDeleting all reservations for showtime {showtime_id}...")
    rows = session.execute("SELECT seat_number FROM reservations WHERE showtime_id = %s", (showtime_id,))
    for row in rows:
        session.execute("DELETE FROM reservations WHERE showtime_id = %s AND seat_number = %s", (showtime_id, row.seat_number))
    print("All reservations deleted.")

# CLI Stress Test Mode
def stress_test_mode(session, showtime_id):
    while True:
        print("\nStress Test Menu")
        print("1. Bulk reservation")
        print("2. Rapid-fire same seat")
        print("3. Random concurrent clients")
        print("4. Competing seat parties")
        print("5. Back to main menu")
        choice = input("Choose (1-5): ").strip()
        if choice == "1":
            stress_test_1(session)
        elif choice == "2":
            stress_test_2(session)
        elif choice == "3":
            stress_test_3(session)
        elif choice == "4":
            stress_test_4(session)
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    print("🎬 Welcome to the Cinema Reservation CLI")
    user_id = input("Enter your user ID: ").strip()
    _, session = connect()
    current_showtime = seed_data(session)

    while True:
        print("\nCinema Main Menu")
        print("1. Regular Use Mode")
        print("2. Stress Test Mode")
        print("3. Exit")
        choice = input("Select (1-3): ").strip()
        if choice == "1":
            regular_use_mode(session, current_showtime, user_id)
        elif choice == "2":
            stress_test_mode(session, current_showtime)
        elif choice == "3":
            print("Goodbye!")
            break

