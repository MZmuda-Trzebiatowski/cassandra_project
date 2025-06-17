-- Keyspace
CREATE KEYSPACE IF NOT EXISTS cinema
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 2
};

-- Movies table
CREATE TABLE IF NOT EXISTS movies (
  movie_id TEXT PRIMARY KEY,
  title TEXT,
  description TEXT
);

-- Showtimes table
CREATE TABLE IF NOT EXISTS showtimes (
  showtime_id TEXT PRIMARY KEY,
  movie_id TEXT,
  start_time TIMESTAMP,
  auditorium TEXT
);

-- Showtimes by movie
CREATE TABLE IF NOT EXISTS showtimes_by_movie (
  movie_id TEXT,
  showtime_id TEXT,
  start_time TIMESTAMP,
  auditorium TEXT,
  PRIMARY KEY (movie_id, showtime_id)
);

-- Reservations
CREATE TABLE IF NOT EXISTS reservations (
  showtime_id TEXT,
  seat_number TEXT,
  user_id TEXT,
  reserved_at TIMESTAMP,
  PRIMARY KEY (showtime_id, seat_number)
);
