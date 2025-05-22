CREATE DATABASE IF NOT EXISTS project;
USE project;

CREATE TABLE IF NOT EXISTS user_details (
    Name VARCHAR(100) NOT NULL,
    Dept VARCHAR(50) NOT NULL,
    Roll VARCHAR(10) PRIMARY KEY,
    pwd VARCHAR(100) NOT NULL,
    hostel varchar(100) NOT NULL,
    Phone varchar(100) NOT NULL
);

select * from user_details;
desc user_details;

CREATE TABLE health_issues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Roll VARCHAR(10),
    Issue TEXT,
    Status VARCHAR(20) DEFAULT 'Pending',
    Date DATETIME,
    Meals varchar(100),
    FOREIGN KEY (Roll) REFERENCES user_details(Roll)
);
desc health_issues;

CREATE TABLE warden (
    username VARCHAR(50) PRIMARY KEY,
    password VARCHAR(100),
    hostel VARCHAR(100)
);
