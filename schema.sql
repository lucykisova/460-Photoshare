CREATE DATABASE IF NOT EXISTS photoshare;

USE photoshare;

DROP TABLE IF EXISTS Photos CASCADE;

DROP TABLE IF EXISTS Users CASCADE;

DROP TABLE IF EXISTS Albums CASCADE;

DROP TABLE IF EXISTS Comments CASCADE;

DROP TABLE IF EXISTS Likes CASCADE;

DROP TABLE IF EXISTS Tags CASCADE;

DROP TABLE IF EXISTS Tagged CASCADE;

DROP TABLE IF EXISTS Friendship CASCADE;

CREATE TABLE Users (
  user_id INT NOT NULL AUTO_INCREMENT,
  gender VARCHAR(6),
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(40) NOT NULL,
  dob DATE NOT NULL,
  hometown VARCHAR(40),
  fname VARCHAR(40) NOT NULL,
  lname VARCHAR(40) NOT NULL,
  PRIMARY KEY (user_id)
);

CREATE TABLE Albums (
  album_id INT AUTO_INCREMENT,
  Name VARCHAR(40) NOT NULL,
  date_of_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
  user_id INT NOT NULL,
  PRIMARY KEY (album_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Photos (
  photo_id INT AUTO_INCREMENT,
  user_id INT,
  caption VARCHAR(200),
  imgdata LONGBLOB,
  album_id INT NOT NULL,
  PRIMARY KEY (photo_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id),
  FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE
);

CREATE TABLE Comments (
  comment_id INT NOT NULL AUTO_INCREMENT,
  text TEXT NOT NULL,
  date DATETIME DEFAULT CURRENT_TIMESTAMP,
  user_id INT NOT NULL,
  photo_id INT NOT NULL,
  PRIMARY KEY (comment_id),
  FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
  FOREIGN KEY (photo_id) REFERENCES Photos (photo_id) ON DELETE CASCADE
);

CREATE TABLE Likes ( 
  user_id INT NOT NULL,
  photo_id INT NOT NULL,
  PRIMARY KEY (photo_id, user_id),
  FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
  FOREIGN KEY (photo_id) REFERENCES Photos (photo_id) ON DELETE CASCADE
);

CREATE TABLE Tags (
  tag_id INT AUTO_INCREMENT,
  name VARCHAR(100),
  PRIMARY KEY (tag_id)
);

CREATE TABLE Tagged (
  photo_id INTEGER,
  tag_id INTEGER,
  PRIMARY KEY (photo_id, tag_id),
  FOREIGN KEY(photo_id) REFERENCES Photos(photo_id),
  FOREIGN KEY(tag_id) REFERENCES Tags (tag_id)
);

CREATE TABLE Friendship (
  UID1 INT NOT NULL,
  UID2 INT NOT NULL,
  CHECK (UID1 <> UID2),
  PRIMARY KEY(UID1, UID2),
  FOREIGN KEY (UID1) REFERENCES Users (user_id) ON DELETE CASCADE,
  FOREIGN KEY (UID2) REFERENCES Users (user_id) ON DELETE CASCADE
);

INSERT INTO Users (email, password, gender, dob, hometown, fname, lname) VALUES ('test@bu.edu', 'test', 'male', '2002-01-24', 'Boston', 'Test', 'User');