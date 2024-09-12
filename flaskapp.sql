-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               8.0.39 - MySQL Community Server - GPL
-- Server OS:                    Win64
-- HeidiSQL Version:             12.8.0.6908
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping database structure for flaskapp
DROP DATABASE IF EXISTS `flaskapp`;
CREATE DATABASE IF NOT EXISTS `flaskapp` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `flaskapp`;

-- Dumping structure for table flaskapp.admin
DROP TABLE IF EXISTS `admin`;
CREATE TABLE IF NOT EXISTS `admin` (
  `id` int NOT NULL,
  `name` varchar(50) NOT NULL,
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table flaskapp.admin: ~3 rows (approximately)
DELETE FROM `admin`;
INSERT INTO `admin` (`id`, `name`, `email`, `password`) VALUES
	(1, '', 'AdminUser', 'adminpass'),
	(2, '2', '2@gmail.com', '$2b$12$JOf9mQbRllsaIxnS5mbM1Ot.Iy6LB658XGvK7iZa8j307.hF9lJzW'),
	(4, '4', '4@gmail.come', '$2b$12$JcnWMpg5p6yLwQ/mSzSa8eTRq81DZQdm7bGNpLZjXFPlmF0esFVs6'),
	(5, '5', '5@gmail.com', '$2b$12$Bh0dX/UR2vZPfGhuLnEHZumXcaN968Bz0RR1MEFtbeXSRUw8vQ9tO'),
	(11, '11', '11@gmail.come', '$2b$12$jIxxu7uar2uAUial7hRPQO8OvxIa1nxz0L7ZK386nzJqUV0Pv70ae'),
	(21, '21', '21@ee', '$2b$12$xRPQOxgtZqYcx.cgOdXEvu7nvCfzcX6fp0jyerynu4FjQ7WrvxBQ.'),
	(123, '123', '1111@gmail.com', '$2b$12$px/ugQJof3k/qP/WvbnXQeHesnj5GOd0glyY1dCr7WOrgXD2Ptg6u'),
	(222, '222', '222@gmail.com', '$2b$12$dUvNvuYjLgkVP3ZfXAqQYeC39Xx61jF04y3CDKYMwfC1vmqqfQ0P6');

-- Dumping structure for table flaskapp.announcement
DROP TABLE IF EXISTS `announcement`;
CREATE TABLE IF NOT EXISTS `announcement` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `context` text COLLATE utf8mb4_unicode_520_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- Dumping data for table flaskapp.announcement: ~0 rows (approximately)
DELETE FROM `announcement`;
INSERT INTO `announcement` (`id`, `title`, `context`) VALUES
	(1, '"Neque porro quisquam est qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit..."', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam non molestie eros. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Vivamus viverra, neque id condimentum consequat, mauris purus auctor magna, at lacinia nulla nisi eu turpis. Maecenas posuere metus velit, eget bibendum diam fermentum at. Nullam egestas tellus risus, fermentum posuere urna egestas non. Morbi sagittis leo nunc, at porta leo accumsan in. Pellentesque vel tristique nulla. Quisque consectetur vestibulum commodo. Etiam vel congue diam. Nunc tincidunt diam eu nunc dictum, et vestibulum dui vestibulum. Pellentesque eu justo eu neque euismod tincidunt.\r\n\r\nProin faucibus fringilla tempus. Donec vehicula neque et nibh ultrices aliquam. Donec non pretium neque. Ut maximus eros nec egestas fringilla. Nulla sed facilisis turpis. Proin viverra risus id lectus rhoncus lobortis. Fusce ut nulla in odio gravida convallis. Quisque tristique nunc non mauris pellentesque dictum. Sed sit amet lorem est. Nam porta dictum congue. Vestibulum sed venenatis diam, rutrum vulputate ipsum. Nullam nisl nunc, cursus et orci quis, dignissim laoreet est. In hac habitasse platea dictumst. Quisque volutpat sit amet nisl ac rutrum. Ut molestie, ligula in egestas convallis, lacus erat condimentum nulla, in dictum tellus quam pulvinar sapien. Praesent orci ligula, aliquam vel finibus sed, scelerisque et orci.'),
	(2, '"Neque porro quisquam est qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit..."', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam non molestie eros. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Vivamus viverra, neque id condimentum consequat, mauris purus auctor magna, at lacinia nulla nisi eu turpis. Maecenas posuere metus velit, eget bibendum diam fermentum at. Nullam egestas tellus risus, fermentum posuere urna egestas non. Morbi sagittis leo nunc, at porta leo accumsan in. Pellentesque vel tristique nulla. Quisque consectetur vestibulum commodo. Etiam vel congue diam. Nunc tincidunt diam eu nunc dictum, et vestibulum dui vestibulum. Pellentesque eu justo eu neque euismod tincidunt.\r\n\r\nProin faucibus fringilla tempus. Donec vehicula neque et nibh ultrices aliquam. Donec non pretium neque. Ut maximus eros nec egestas fringilla. Nulla sed facilisis turpis. Proin viverra risus id lectus rhoncus lobortis. Fusce ut nulla in odio gravida convallis. Quisque tristique nunc non mauris pellentesque dictum. Sed sit amet lorem est. Nam porta dictum congue. Vestibulum sed venenatis diam, rutrum vulputate ipsum. Nullam nisl nunc, cursus et orci quis, dignissim laoreet est. In hac habitasse platea dictumst. Quisque volutpat sit amet nisl ac rutrum. Ut molestie, ligula in egestas convallis, lacus erat condimentum nulla, in dictum tellus quam pulvinar sapien. Praesent orci '),
	(3, 'zd', 'sdf'),
	(4, 'sdfsdf', 'sfsdf');

-- Dumping structure for table flaskapp.beds
DROP TABLE IF EXISTS `beds`;
CREATE TABLE IF NOT EXISTS `beds` (
  `id` int NOT NULL AUTO_INCREMENT,
  `room_number` int NOT NULL,
  `bed_letter` char(1) NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Available',
  PRIMARY KEY (`id`),
  UNIQUE KEY `room_bed` (`room_number`,`bed_letter`),
  CONSTRAINT `fk_beds_rooms` FOREIGN KEY (`room_number`) REFERENCES `rooms` (`number`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table flaskapp.beds: ~16 rows (approximately)
DELETE FROM `beds`;
INSERT INTO `beds` (`id`, `room_number`, `bed_letter`, `status`) VALUES
	(1, 101, 'A', 'Available'),
	(2, 102, 'A', 'Available'),
	(3, 103, 'A', 'Available'),
	(4, 104, 'A', 'Available'),
	(5, 201, 'A', 'Available'),
	(6, 202, 'A', 'Available'),
	(7, 203, 'A', 'Available'),
	(8, 301, 'A', 'Available'),
	(9, 302, 'A', 'Available'),
	(10, 303, 'A', 'Available'),
	(11, 102, 'B', 'Available'),
	(12, 103, 'B', 'Available'),
	(13, 104, 'B', 'Available'),
	(14, 202, 'B', 'Available'),
	(15, 203, 'B', 'Available'),
	(16, 302, 'B', 'Available'),
	(17, 303, 'B', 'Available'),
	(18, 103, 'C', 'Available'),
	(19, 203, 'C', 'Available'),
	(20, 303, 'C', 'Available');

-- Dumping structure for table flaskapp.booking
DROP TABLE IF EXISTS `booking`;
CREATE TABLE IF NOT EXISTS `booking` (
  `booking_no` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `trimester_id` int NOT NULL,
  `group_individual` tinyint(1) NOT NULL,
  `group_id` int DEFAULT NULL,
  `hostel_id` int NOT NULL,
  `room_no` int NOT NULL,
  `cost` decimal(10,2) NOT NULL,
  `bed_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  PRIMARY KEY (`booking_no`),
  KEY `FK_booking_trimester` (`trimester_id`),
  KEY `FK_booking_users` (`user_id`),
  KEY `FK_booking_rooms` (`room_no`),
  KEY `FK_booking_hostel` (`hostel_id`),
  KEY `FK_booking_groups` (`group_id`),
  CONSTRAINT `FK_booking_groups` FOREIGN KEY (`group_id`) REFERENCES `groups` (`group_id`),
  CONSTRAINT `FK_booking_hostel` FOREIGN KEY (`hostel_id`) REFERENCES `hostel` (`id`),
  CONSTRAINT `FK_booking_rooms` FOREIGN KEY (`room_no`) REFERENCES `rooms` (`number`),
  CONSTRAINT `FK_booking_trimester` FOREIGN KEY (`trimester_id`) REFERENCES `trimester` (`id`),
  CONSTRAINT `FK_booking_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=93 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- Dumping data for table flaskapp.booking: ~0 rows (approximately)
DELETE FROM `booking`;

-- Dumping structure for table flaskapp.groups
DROP TABLE IF EXISTS `groups`;
CREATE TABLE IF NOT EXISTS `groups` (
  `group_id` int NOT NULL AUTO_INCREMENT,
  `leader_id` int NOT NULL,
  `trimester` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  PRIMARY KEY (`group_id`),
  KEY `leader_id` (`leader_id`),
  CONSTRAINT `groups_ibfk_1` FOREIGN KEY (`leader_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- Dumping data for table flaskapp.groups: ~0 rows (approximately)
DELETE FROM `groups`;

-- Dumping structure for table flaskapp.group_members
DROP TABLE IF EXISTS `group_members`;
CREATE TABLE IF NOT EXISTS `group_members` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `group_id` (`group_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `group_members_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`group_id`),
  CONSTRAINT `group_members_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=72 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- Dumping data for table flaskapp.group_members: ~0 rows (approximately)
DELETE FROM `group_members`;

-- Dumping structure for table flaskapp.hostel
DROP TABLE IF EXISTS `hostel`;
CREATE TABLE IF NOT EXISTS `hostel` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `gender` enum('Male','Female') NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table flaskapp.hostel: ~4 rows (approximately)
DELETE FROM `hostel`;
INSERT INTO `hostel` (`id`, `name`, `gender`) VALUES
	(1, 'Hostel A', 'Male'),
	(2, 'Hostel B', 'Female'),
	(3, 'Hostel C', 'Male'),
	(4, 'Hostel D', 'Female');

-- Dumping structure for table flaskapp.rooms
DROP TABLE IF EXISTS `rooms`;
CREATE TABLE IF NOT EXISTS `rooms` (
  `number` int NOT NULL,
  `hostel_id` int NOT NULL,
  `category` varchar(20) NOT NULL,
  `capacity` int NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Available',
  `price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`number`),
  KEY `hostel_id` (`hostel_id`),
  CONSTRAINT `rooms_ibfk_1` FOREIGN KEY (`hostel_id`) REFERENCES `hostel` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table flaskapp.rooms: ~23 rows (approximately)
DELETE FROM `rooms`;
INSERT INTO `rooms` (`number`, `hostel_id`, `category`, `capacity`, `status`, `price`) VALUES
	(101, 1, 'Single', 1, 'Available', 100.00),
	(102, 1, 'Double', 2, 'Available', 150.00),
	(103, 1, 'Triple', 3, 'Available', 200.00),
	(104, 1, 'Double', 2, 'Available', 200.00),
	(105, 1, 'Double', 2, 'Available', 200.00),
	(106, 1, 'Single', 1, 'Available', 100.00),
	(107, 1, 'Double', 2, 'Available', 150.00),
	(108, 1, 'Triple', 3, 'Available', 200.00),
	(201, 2, 'Single', 1, 'Available', 110.00),
	(202, 2, 'Double', 2, 'Available', 160.00),
	(203, 2, 'Triple', 3, 'Available', 210.00),
	(204, 2, 'Single', 1, 'Available', 110.00),
	(205, 2, 'Double', 2, 'Available', 160.00),
	(206, 2, 'Triple', 3, 'Available', 210.00),
	(301, 3, 'Single', 1, 'Available', 120.00),
	(302, 3, 'Double', 2, 'Available', 170.00),
	(303, 3, 'Triple', 3, 'Available', 220.00),
	(304, 3, 'Single', 1, 'Available', 120.00),
	(305, 3, 'Double', 2, 'Available', 170.00),
	(306, 3, 'Triple', 3, 'Available', 220.00),
	(307, 3, 'Single', 1, 'Available', 120.00),
	(308, 3, 'Double', 2, 'Available', 170.00),
	(309, 3, 'Triple', 3, 'Available', 220.00);

-- Dumping structure for table flaskapp.trimester
DROP TABLE IF EXISTS `trimester`;
CREATE TABLE IF NOT EXISTS `trimester` (
  `id` int NOT NULL AUTO_INCREMENT,
  `term` int NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- Dumping data for table flaskapp.trimester: ~3 rows (approximately)
DELETE FROM `trimester`;
INSERT INTO `trimester` (`id`, `term`, `name`) VALUES
	(1, 2310, 'Trimester March/April 2024'),
	(2, 2320, 'Trimester July/August 2024'),
	(3, 2330, 'Trimester Oct/Nov 2024');

-- Dumping structure for table flaskapp.users
DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `gender` enum('Male','Female') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `email` varchar(50) NOT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `faculty` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `profile_pic` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table flaskapp.users: ~18 rows (approximately)
DELETE FROM `users`;
INSERT INTO `users` (`id`, `name`, `gender`, `email`, `password`, `faculty`, `profile_pic`) VALUES
	(1, 'John Wick', 'Male', '1@example.com', '$2b$12$yocdymDGgMbzktihJhXTguo7yuDDCMWSensxIX75HTBA1RkfyZ7zi', 'Computing', ''),
	(2, 'Jane Smith', 'Female', 'user2@example.com', 'password2', 'Science', ''),
	(3, 'Bob Johnson', 'Male', 'user3@example.com', '$2b$12$JM.1cbG9FfxI25htADx53.6uJ95x28nFq1ze0Qz/v4m/gpy1cqhkm', 'Arts', ''),
	(4, 'Alice Cooper', 'Female', 'alice.cooper@example.com', 'password4', 'Business', ''),
	(5, 'David Miller', 'Male', 'david.miller@example.com', 'password5', 'Mathematics', ''),
	(6, 'Emma Watson', 'Female', 'emma.watson@example.com', 'password6', 'Computer Science', ''),
	(7, 'Liam Nelson', 'Male', 'liam.nelson@example.com', 'password7', 'Physics', ''),
	(8, 'Sophia Lee', 'Female', 'sophia.lee@example.com', 'password8', 'Biology', ''),
	(9, 'Noah Brown', 'Male', 'noah.brown@example.com', 'password9', 'History', ''),
	(10, 'Olivia Martin', 'Female', 'olivia.martin@example.com', 'password10', 'Chemistry', ''),
	(11, 'William Davis', 'Male', 'william.davis@example.com', 'password11', 'Engineering', ''),
	(12, 'Isabella Garcia', 'Female', 'isabella.garcia@example.com', 'password12', 'Psychology', ''),
	(13, 'James Wilson', 'Male', 'james.wilson@example.com', 'password13', 'Philosophy', ''),
	(14, 'Charlotte Martinez', 'Female', 'charlotte.martinez@example.com', 'password14', 'Art', ''),
	(15, 'Michael Anderson', 'Male', 'michael.anderson@example.com', 'password15', 'Business', ''),
	(16, 'WAKABAKA', 'Male', 'userNick@example.com', 'password1', 'Engineering', ''),
	(111, NULL, 'Male', '1@sample.com', '$2b$12$UxNpvG4rGzjdPVd2LFfI8eaUW1JVKspVfeC8w7Zh9HikITqO31A4y', NULL, NULL),
	(4444, NULL, 'Male', '4444@gmail.com', '$2b$12$tYbW4Cg7mhobKPxJseUW8uyWMmTR0FR/rpj.ifSJakj/SmZIZoQOq', NULL, NULL);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
