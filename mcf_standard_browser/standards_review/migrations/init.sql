DROP TABLE IF EXISTS `Standard_Library_MCF_Inhouse_metabolites`;
CREATE TABLE `Standard_Library_MCF_Inhouse_metabolites` (
  `id` int(11) NOT NULL,
  `name` linestring NOT NULL,
  `formula` linestring NOT NULL,
  `inchi` linestring DEFAULT NULL,
  `solubility` linestring DEFAULT NULL,
  `vendor` linestring DEFAULT NULL,
  `vendor_id` int(11) DEFAULT NULL,
  `hmbd_id` linestring DEFAULT NULL,
  `chebi_id` int(11) DEFAULT NULL,
  `lipidmaps_id` linestring DEFAULT NULL,
  `cas_id` linestring DEFAULT NULL,
  `pubchem_id` linestring DEFAULT NULL,
  `lot_num` linestring DEFAULT NULL,
  `location` linestring DEFAULT NULL,
  `purchase_date` linestring DEFAULT NULL,
  `Average Molecular weight (g/mol)` float DEFAULT NULL,
  `Exact mass` float DEFAULT NULL,
  `m/z_Neg mode` float DEFAULT NULL,
  `m/z_Pos Mode` float DEFAULT NULL,
  `Adducts Na` linestring DEFAULT NULL,
  `Adducts NH4` linestring DEFAULT NULL,
  `Class` linestring DEFAULT NULL,
  `Retention time` float DEFAULT NULL,
  `Date of Prep` linestring DEFAULT NULL,
  `Protocol ID` linestring DEFAULT NULL,
  `Comments` linestring DEFAULT NULL,
  `Sample weight for stock (mg)` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `standards_review_adduct_id_uindex` (`id`)
);

DROP TABLE IF EXISTS `standards_review_adduct`;
CREATE TABLE `standards_review_adduct` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `delta_atoms` longtext NOT NULL,
  `charge` int(11) NOT NULL,
  `delta_formula` longtext NOT NULL,
  `nM` int(11) NOT NULL,
  PRIMARY KEY (`id`)
);

DROP TABLE IF EXISTS `standards_review_dataset`;
CREATE TABLE `standards_review_dataset` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` longtext NOT NULL,
  `mass_accuracy_ppm` double NOT NULL,
  `quad_window_mz` double NOT NULL,
  `intrument` longtext NOT NULL,
  `processing_finished` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
);

DROP TABLE IF EXISTS `standards_review_dataset_adducts_present`;
CREATE TABLE `standards_review_dataset_adducts_present` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dataset_id` int(11) NOT NULL,
  `adduct_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `standards_review_dataset_adducts_presen_dataset_id_9b025de5_uniq` (`dataset_id`,`adduct_id`),
  KEY `standards_revie_adduct_id_dbd73de6_fk_standards_review_adduct_id` (`adduct_id`),
  CONSTRAINT `standards_revie_adduct_id_dbd73de6_fk_standards_review_adduct_id` FOREIGN KEY (`adduct_id`) REFERENCES `standards_review_adduct` (`id`),
  CONSTRAINT `standards_rev_dataset_id_90ed766e_fk_standards_review_dataset_id` FOREIGN KEY (`dataset_id`) REFERENCES `standards_review_dataset` (`id`)
);

DROP TABLE IF EXISTS `standards_review_dataset_standards_present`;
CREATE TABLE `standards_review_dataset_standards_present` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dataset_id` int(11) NOT NULL,
  `standard_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `standards_review_dataset_standards_pres_dataset_id_d98826a5_uniq` (`dataset_id`,`standard_id`),
  KEY `standards_r_standard_id_c5bf6e76_fk_standards_review_standard_id` (`standard_id`),
  CONSTRAINT `standards_rev_dataset_id_c017d194_fk_standards_review_dataset_id` FOREIGN KEY (`dataset_id`) REFERENCES `standards_review_dataset` (`id`),
  CONSTRAINT `standards_r_standard_id_c5bf6e76_fk_standards_review_standard_id` FOREIGN KEY (`standard_id`) REFERENCES `standards_review_standard` (`id`)
);

DROP TABLE IF EXISTS `standards_review_fragmentationspectrum`;
CREATE TABLE `standards_review_fragmentationspectrum` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `precursor_mz` double DEFAULT NULL,
  `_centroid_mzs` longtext NOT NULL,
  `_centroid_ints` longtext NOT NULL,
  `spec_num` int(11) DEFAULT NULL,
  `dataset_id` int(11) NOT NULL,
  `standard_id` int(11) DEFAULT NULL,
  `rt` double,
  `adduct_id` int(11),
  `precursor_quad_fraction` double,
  `reviewed` tinyint(1) NOT NULL,
  `date_added` date NOT NULL,
  `date_edited` date NOT NULL,
  `last_editor_id` int(11),
  `collision_energy` longtext NOT NULL,
  `ms1_intensity` double NOT NULL,
  PRIMARY KEY (`id`),
  KEY `standards_rev_dataset_id_24102ea5_fk_standards_review_dataset_id` (`dataset_id`),
  KEY `standards_r_standard_id_a0893bed_fk_standards_review_standard_id` (`standard_id`),
  KEY `standards_review_fragmentationspectrum_fd7ccddf` (`adduct_id`),
  KEY `standards_review_fragmentationspectrum_292dbdb3` (`last_editor_id`),
  CONSTRAINT `standards_review_fragmen_last_editor_id_40dcbb6d_fk_auth_user_id` FOREIGN KEY (`last_editor_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `standards_revie_adduct_id_b0d6304c_fk_standards_review_adduct_id` FOREIGN KEY (`adduct_id`) REFERENCES `standards_review_adduct` (`id`),
  CONSTRAINT `standards_rev_dataset_id_24102ea5_fk_standards_review_dataset_id` FOREIGN KEY (`dataset_id`) REFERENCES `standards_review_dataset` (`id`),
  CONSTRAINT `standards_r_standard_id_a0893bed_fk_standards_review_standard_id` FOREIGN KEY (`standard_id`) REFERENCES `standards_review_standard` (`id`)
);

DROP TABLE IF EXISTS `standards_review_molecule`;
CREATE TABLE `standards_review_molecule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `_adduct_mzs` longtext NOT NULL,
  `name` longtext NOT NULL,
  `sum_formula` longtext,
  `inchi_code` longtext NOT NULL,
  `exact_mass` double NOT NULL,
  `solubility` longtext,
  `hmdb_id` longtext,
  `chebi_id` longtext,
  `lipidmaps_id` longtext,
  `cas_id` longtext,
  `pubchem_id` longtext,
  PRIMARY KEY (`id`)
);

DROP TABLE IF EXISTS `standards_review_standard`;
CREATE TABLE `standards_review_standard` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `location` longtext,
  `lot_num` longtext,
  `vendor` longtext,
  `vendor_cat` longtext,
  `purchase_date` date,
  `molecule_id` int(11) NOT NULL,
  `MCFID` int(11),
  PRIMARY KEY (`id`),
  KEY `standards_review_standard_a5836404` (`molecule_id`)
);

DROP TABLE IF EXISTS `standards_review_xic`;
CREATE TABLE `standards_review_xic` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mz` double NOT NULL,
  `data` longtext NOT NULL,
  `adduct_id` int(11) DEFAULT NULL,
  `dataset_id` int(11) NOT NULL,
  `standard_id` int(11) DEFAULT NULL,
  `rt_data` longtext NOT NULL,
  `collision` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `standards_revie_adduct_id_a78bbb50_fk_standards_review_adduct_id` (`adduct_id`),
  KEY `standards_r_standard_id_f485dcf3_fk_standards_review_standard_id` (`standard_id`),
  KEY `standards_review_xic_dataset_id_f460ff0f_uniq` (`dataset_id`),
  CONSTRAINT `standards_revie_adduct_id_a78bbb50_fk_standards_review_adduct_id` FOREIGN KEY (`adduct_id`) REFERENCES `standards_review_adduct` (`id`),
  CONSTRAINT `standards_rev_dataset_id_f460ff0f_fk_standards_review_dataset_id` FOREIGN KEY (`dataset_id`) REFERENCES `standards_review_dataset` (`id`),
  CONSTRAINT `standards_r_standard_id_f485dcf3_fk_standards_review_standard_id` FOREIGN KEY (`standard_id`) REFERENCES `standards_review_standard` (`id`)
);