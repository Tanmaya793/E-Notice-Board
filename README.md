# E-Notice-Board
A online notice board system
Try creating your database before running the project.
The code snippet for the databse will be down below.
\use notice_board;

CREATE TABLE users(
id INT AUTO_INCREMENT PRIMARY KEY,
full_name varchar(51),
email varchar(100),
password varchar(30),
user_type varchar(20),
course varchar(30),
phone BIGINT,
branch varchar(30),
roll_number varchar(10),
designation varchar(20),
subject varchar(30),
batch varchar(15),
recovery_pin INT
);
select * from users;

CREATE TABLE notice(
notice_id INT PRIMARY KEY AUTO_INCREMENT,
title varchar(50),
content varchar(1000),
date_posted DATE,
exp_date DATE,
posted_by INT,
FOREIGN KEY (posted_by) REFERENCES users (id)
);

SELECT * FROM notice;

desc recepient;
CREATE TABLE recepient(
rec_id INT PRIMARY KEY AUTO_INCREMENT,
notice_id INT,
user_id INT,
status VARCHAR(10),
FOREIGN KEY (notice_id) REFERENCES notice (notice_id),
FOREIGN KEY (user_id) REFERENCES users (id)
);
SELECT * FROM recepient;

CREATE TABLE sent(
sent_id INT AUTO_INCREMENT PRIMARY KEY,
notice_id INT,
sent_to INT,
FOREIGN KEY (notice_id) REFERENCES notice (notice_id),
FOREIGN KEY (sent_to) REFERENCES users (id)
);
SELECT * FROM sent;

CREATE TABLE notice_creation(
n_id INT PRIMARY KEY,
u_id INT,
FOREIGN KEY (n_id) references notice (notice_id),
FOREIGN KEY (u_id) references users (id)
);
SELECT * FROM notice_creation;

CREATE TABLE receives(
rec_id INT PRIMARY KEY,
u_id INT,
FOREIGN KEY (rec_id) references recepient (rec_id),
FOREIGN KEY (u_id) references users (id)
);
SELECT * FROM receives;

CREATE TABLE notice_recepient(
rec_id INT,
n_id INT,
FOREIGN KEY (rec_id) references recepient (rec_id),
FOREIGN KEY (n_id) references notice (notice_id)
);
SELECT * FROM notice_recepient;


//As it is a leaning project, any suggestion is welcomed.
