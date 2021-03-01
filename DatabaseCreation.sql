CREATE DATABASE `polymap` /*!40100 DEFAULT CHARACTER SET utf8 */ /*!80016 DEFAULT ENCRYPTION='N' */;
CREATE TABLE `people` (
  `id` int NOT NULL AUTO_INCREMENT,
  `label` varchar(45) DEFAULT NULL,
  `discordTag` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8;
CREATE TABLE `relationships` (
  `idrelationships` int NOT NULL AUTO_INCREMENT,
  `person1` int NOT NULL,
  `person2` int NOT NULL,
  `start` date DEFAULT NULL,
  `stop` date DEFAULT NULL,
  PRIMARY KEY (`idrelationships`),
  KEY `person1_idx` (`person1`),
  KEY `person2_idx` (`person2`),
  CONSTRAINT `person1` FOREIGN KEY (`person1`) REFERENCES `people` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `person2` FOREIGN KEY (`person2`) REFERENCES `people` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;
