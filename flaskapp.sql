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
CREATE DATABASE IF NOT EXISTS `flaskapp` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `flaskapp`;

-- Dumping structure for table flaskapp.admin
CREATE TABLE IF NOT EXISTS `admin` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `password` varchar(50) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- Dumping data for table flaskapp.admin: ~0 rows (approximately)
INSERT INTO `admin` (`id`, `name`, `password`) VALUES
	('9900', 'Admin', '12345');

-- Dumping structure for table flaskapp.rooms
CREATE TABLE IF NOT EXISTS `rooms` (
  `number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL DEFAULT '',
  `category` varchar(50) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `capacity` int DEFAULT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `cost` int DEFAULT NULL,
  `chosen_by` varchar(50) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  PRIMARY KEY (`number`),
  KEY `FK_rooms_users` (`chosen_by`),
  CONSTRAINT `FK_rooms_users` FOREIGN KEY (`chosen_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- Dumping data for table flaskapp.rooms: ~1 rows (approximately)
INSERT INTO `rooms` (`number`, `category`, `capacity`, `status`, `cost`, `chosen_by`) VALUES
	('123', 'Single', 1, 'Available', 500, NULL);

-- Dumping structure for table flaskapp.users
CREATE TABLE IF NOT EXISTS `users` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL DEFAULT '',
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `gender` varchar(50) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `password` varchar(50) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- Dumping data for table flaskapp.users: ~1 rows (approximately)
INSERT INTO `users` (`id`, `email`, `gender`, `password`) VALUES
	('1231102119', '123@gmail.com', 'male', '123');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
