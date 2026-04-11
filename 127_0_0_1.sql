-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Apr 11, 2026 at 11:40 AM
-- Server version: 8.3.0
-- PHP Version: 8.2.18

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `ecommerce_db`
--
CREATE DATABASE IF NOT EXISTS `ecommerce_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `ecommerce_db`;

-- --------------------------------------------------------

--
-- Table structure for table `cart_items`
--

DROP TABLE IF EXISTS `cart_items`;
CREATE TABLE IF NOT EXISTS `cart_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `product_id` int NOT NULL,
  `quantity` int DEFAULT '1',
  `added_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `product_id` (`product_id`)
) ENGINE=MyISAM AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `cart_items`
--

INSERT INTO `cart_items` (`id`, `user_id`, `product_id`, `quantity`, `added_at`) VALUES
(1, 24, 1, 2, '2025-11-13 10:49:10'),
(2, 25, 1, 3, '2025-11-13 12:15:35'),
(3, 25, 2, 1, '2025-11-13 12:59:26'),
(4, 25, 7, 5, '2025-11-13 13:32:40'),
(5, 19, 7, 1, '2025-11-13 13:34:01'),
(6, 26, 7, 2, '2025-11-13 13:49:42'),
(7, 29, 14, 2, '2025-01-18 12:59:52'),
(8, 29, 11, 1, '2025-01-18 15:04:11'),
(9, 29, 9, 1, '2025-01-18 15:09:02'),
(10, 29, 13, 3, '2025-01-18 15:16:27'),
(11, 31, 13, 2, '2025-01-18 21:48:06'),
(12, 31, 12, 3, '2025-01-18 21:52:12');

-- --------------------------------------------------------

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
CREATE TABLE IF NOT EXISTS `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `order_items`
--

DROP TABLE IF EXISTS `order_items`;
CREATE TABLE IF NOT EXISTS `order_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `product_id` int NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `quantity` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `order_id` (`order_id`),
  KEY `product_id` (`product_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
CREATE TABLE IF NOT EXISTS `products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `price` decimal(10,2) NOT NULL,
  `stock` int DEFAULT '0',
  `image` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `products`
--

INSERT INTO `products` (`id`, `name`, `slug`, `category`, `description`, `price`, `stock`, `image`, `created_at`) VALUES
(1, 'iphone 16 pro max', '', 'all categories', '', 10000000.00, 50, NULL, '2025-11-13 10:45:21'),
(2, 'shoe', '', 'all categories', 'brown long', 5000.00, 100, NULL, '2025-11-13 12:57:54'),
(3, 'Shirt', '', 'all categories', '', 3000.00, 500, NULL, '2025-11-13 12:58:48'),
(4, 'tablet', '', 'all categories', '', 400.00, 50, NULL, '2025-11-13 13:07:36'),
(5, 'samsung galaxy A14', '', 'all categories', '', 25000.00, 30, NULL, '2025-11-13 13:28:15'),
(6, 'shoe', '', 'all categories', '', 5000.00, 1000, 'uploads/africanwildlife3.jpg', '2025-11-13 13:29:14'),
(7, 'Balenciaga', '', 'all categories', '', 20000.00, 500, NULL, '2025-11-13 13:31:25'),
(8, 'gold necklace', '', 'all categories', 'gold', 20.00, 200, NULL, '2025-11-22 15:18:17'),
(9, 'laptop', '', '', '', 200.00, 50, NULL, '2025-12-13 05:44:53'),
(10, 'lip gloss', '', '', '', 50.00, 700, NULL, '2025-12-13 05:46:28'),
(11, 'sense', '', 'All categories', '', 1000.00, 30, NULL, '2025-12-13 05:56:09'),
(12, 'sense', '', 'All categories', '', 1000.00, 30, NULL, '2025-12-13 05:56:30'),
(13, 'Naked Wolfe', '', 'All categories', '', 25000.00, 2000, NULL, '2025-12-13 09:50:06'),
(14, 'Iphone 17 Pro', '', 'All categories', '', 20000.00, 19500, NULL, '2025-12-13 09:57:18'),
(15, 'generator', '', 'All categories', '', 13400.00, 50, 'uploads/20240809_085955.jpg', '2025-01-18 22:01:56'),
(16, 'solar', '', 'All categories', '', 4000.00, 300, 'uploads/20250316_074007.jpg', '2025-01-18 22:04:47'),
(17, 'solar', '', 'All categories', '', 4000.00, 300, 'uploads/20250316_074007.jpg', '2025-01-18 22:05:17'),
(18, 'solar', '', 'All categories', '', 4000.00, 300, 'uploads/20250316_074007.jpg', '2025-01-18 22:05:43');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` enum('admin','user','','') COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_admin` tinyint DEFAULT '0',
  `is_delete` tinyint(1) NOT NULL DEFAULT '1',
  `deleted_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=MyISAM AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `is_admin`, `is_delete`, `deleted_at`, `created_at`) VALUES
(25, 'LILIAN', 'lilie4inans@gmail.com', 'pbkdf2:sha256:260000$CH1ZdIT93fCQEoGj$569587a47e3221d60a15d7d6d0288e1718699d3500d8dd76ffb08986dd965fd9', 'admin', 1, 1, NULL, '2025-11-13 12:10:20'),
(24, 'iya jay', 'o2025@gmail.com', 'pbkdf2:sha256:260000$G3RgM5DGXaINIsaS$59d7f60a5aa9c90b1b0247425923dd7eceac1311a6fd58d22a66701c025b29d5', 'admin', 1, 1, NULL, '2025-11-13 09:10:20'),
(23, 'ene', '2025@gmail.com', 'pbkdf2:sha256:260000$7yHFG2xvkIatTkOU$df9210e24008e12c44e215b90e00102ca68cd7baa1d638813fe7314f3b0b6bb3', 'user', 0, 1, NULL, '2025-11-08 18:24:15'),
(22, 'oloche', '5@gmail.com', 'pbkdf2:sha256:260000$foVY7cWPJBg9EU5d$31550efb3320d5169f46bf9b0ef722ac7d31a5f353a5fd8980ffedbd35d7d4f1', 'admin', 1, 1, NULL, '2025-11-08 18:23:20'),
(21, 'iya jay', 'ia2025@gmail.com', 'pbkdf2:sha256:260000$2Bx2XizhBdqfBZgR$e8e790ee5c21785abd8d6fb4241d798950aeefd97e47d482055877a402ecf65b', 'admin', 1, 1, NULL, '2025-11-08 12:44:07'),
(20, 'oloche', '77@gmail.com', 'pbkdf2:sha256:260000$YTZcJvuhprl20jJ9$0f605bf7f694e118d4eda15440e2a6de6b78f0ed266a3f9bad9e91abfc0d6bb8', 'admin', 1, 1, NULL, '2025-11-04 01:41:50'),
(19, 'idoko', 'owoichoidokowoicho2025@gmail.com', 'pbkdf2:sha256:260000$x8jMK4GYQORXasTr$a517c1a3d844795f5f8af5293cf1e2444600481b4c2f510e6d367c80bc0932c2', 'user', 0, 1, NULL, '2025-11-04 01:34:54'),
(26, '5', 'owoicho2025@gmail.com', 'pbkdf2:sha256:260000$YYye7XU1sRPpS0nV$e634f80e8568ac620bb727a84a5b2c45f3d699918168f8744c9bfd22e0bb2523', 'admin', 1, 1, NULL, '2025-11-13 13:49:01'),
(27, 'i', '25@gmail.com', 'pbkdf2:sha256:260000$pJbqWnxPFXX8GZxj$2502bcd7a5da2c1d4a5468f59b52de7d810c62a02ba79a7441e36473f1fdf877', 'admin', 1, 1, NULL, '2025-12-13 05:23:18'),
(28, '12345678', '12345678@gmail.com', 'pbkdf2:sha256:260000$C5yG3ZjOKFMcRc76$8f79bb39c2eb98eb77f5220a575efc10094c387a57c5d642b891cfd5f4888496', 'admin', 1, 1, NULL, '2025-12-13 05:30:00'),
(29, 'tunde', 'tunde25@gmail.com', 'pbkdf2:sha256:260000$tES2Yot0AH3briVZ$3ace0a427923efffaf2eccf21a0566b3b235d75934f3538f2d949efb619d81eb', 'admin', 1, 1, NULL, '2025-12-13 06:12:16'),
(30, '1234578', '1234578@gmail.com', 'pbkdf2:sha256:260000$9VRd4AvLQvwYxF5R$79f5482d88f7a62d36a0ad265e2caa8aa33cbff6de37010e1c229b3dd99cd60b', 'admin', 0, 1, NULL, '2025-01-18 13:12:24'),
(31, 'ijkl', 'ijkl@gmail.com', 'pbkdf2:sha256:260000$BqZGQmxYrED1W2v7$80d0371129d25df03c2c1415115656793c497d614497261110735ac65f7a4bdf', 'admin', 0, 1, NULL, '2025-01-18 21:47:15');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
