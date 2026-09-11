-- MySQL dump 10.13  Distrib 8.0.46, for Linux (aarch64)
--
-- Host: localhost    Database: rfihunter
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `rfihunter`
--

/*!40000 DROP DATABASE IF EXISTS `rfihunter`*/;

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `rfihunter` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `rfihunter`;

--
-- Table structure for table `industry_areas`
--

DROP TABLE IF EXISTS `industry_areas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `industry_areas` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=83 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `locations` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=116 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `scrape_runs`
--

DROP TABLE IF EXISTS `scrape_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `scrape_runs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `source` varchar(100) NOT NULL,
  `started_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `finished_at` timestamp NULL DEFAULT NULL,
  `records_new` int unsigned DEFAULT '0',
  `records_upd` int unsigned DEFAULT '0',
  `records_err` int unsigned DEFAULT '0',
  `error_msg` text,
  `status` enum('RUNNING','SUCCESS','FAILED') NOT NULL DEFAULT 'RUNNING',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=74 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tenders`
--

DROP TABLE IF EXISTS `tenders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tenders` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `external_id` varchar(255) NOT NULL,
  `source` varchar(100) NOT NULL,
  `type` enum('RFI','RFP','OTHER') NOT NULL DEFAULT 'OTHER',
  `status` enum('OPEN','CLOSED','UNKNOWN') NOT NULL DEFAULT 'UNKNOWN',
  `title` varchar(1000) NOT NULL,
  `description` mediumtext,
  `contracting_authority` varchar(500) DEFAULT NULL,
  `company_size` enum('SME','LARGE','ANY','UNKNOWN') NOT NULL DEFAULT 'UNKNOWN',
  `industry_area_id` smallint unsigned DEFAULT NULL,
  `location_id` smallint unsigned DEFAULT NULL,
  `published_date` date DEFAULT NULL,
  `deadline_date` date DEFAULT NULL,
  `estimated_value` decimal(18,2) DEFAULT NULL,
  `currency` varchar(10) DEFAULT 'EUR',
  `source_url` varchar(2000) NOT NULL,
  `cpv_codes` json DEFAULT NULL,
  `keywords` json DEFAULT NULL,
  `buyer_email` varchar(500) DEFAULT NULL,
  `buyer_phone` varchar(100) DEFAULT NULL,
  `pdf_urls` json DEFAULT NULL,
  `raw_data` json DEFAULT NULL,
  `opportunity_score` tinyint unsigned DEFAULT '0',
  `related_tender_id` bigint unsigned DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_source_external` (`source`,`external_id`),
  KEY `idx_type` (`type`),
  KEY `idx_status` (`status`),
  KEY `idx_industry` (`industry_area_id`),
  KEY `idx_location` (`location_id`),
  KEY `idx_deadline` (`deadline_date`),
  KEY `idx_published` (`published_date`),
  KEY `idx_company_sz` (`company_size`),
  KEY `idx_opp_score` (`opportunity_score`),
  FULLTEXT KEY `ft_title_desc` (`title`,`description`),
  CONSTRAINT `fk_industry` FOREIGN KEY (`industry_area_id`) REFERENCES `industry_areas` (`id`),
  CONSTRAINT `fk_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16365 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-10 13:12:52
