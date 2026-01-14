# FEATURE.md - Projet Web M2 AMI2B : Application d'assemblage de plasmides

## Fonctionnalités Principales

### 1. **Gestion des Templates de Campagne**
Sur cette page, un utilisateur peut consulter tous les templates de campagnes qui lui sont disponibles. Il peut appliquer des filtres pour étailler sa recherche d'un template particulier. Et créer un template de campagne. 
Si un template l'intéresse, il peut accéder à plus de détails en cliquant sur le template. Sur la page détaillé, il a la possibilité de le modifier, le télécharger.

- **Liste de templates** : Présence des templates de campagnes disponibles pour un utilisateur
- **Création de templates** : Formulaires pour créer des templates de campagne (typés ou non).
- **Téléchargement de templates** : Export en format XLSX pour remplissage hors ligne.

### 2. **Gestion des Collections de Plasmides** 
Pas encore dans la maquette mais l'interface sera proche de l'interface simulation et Gestion des templates
- **Collections publiques** : Accès aux collections publiques (ex: pYTK, pYS) et aux templates publics.
- **Collections privées** : Utilisateurs connectés peuvent sauvegarder et gérer leurs propres collections de plasmides et fichiers de correspondance.
- **Gestion des conflits** : Détection et gestion des conflits de correspondance (ex: même séquence avec des identifiants différents).

### 3. **Simulation et Analyse**
Sur cette page, un utilisateur peut consulter tous les résultats de simulations de campagnes qui lui sont disponibles. Il peut appliquer des filtres pour étailler sa recherche. Et lancer une simulation avec ses propres fichiers/templates de campagne. 
Si un résultats l'intéresse, il peut accéder à plus de détails en cliquant sur le résultats. Sur la page des résultats détaillés, il a la possibilité de compléter/modifier la simulation avec 
- **Simulation de campagne** : Simulation des gels d'électrophorèse et calcul des dilutions à partir d’un template rempli, d’une archive de séquences (GenBank), et de fichiers de correspondance.

### 4. **Authentification et Rôles**
Accessible dans la page profile
- **Utilisateurs non connectés** : Accès limité (téléchargement de templates publics, simulation de campagne).
- **Utilisateurs connectés** : Sauvegarde des collections, gestion des équipes, et accès aux fonctionnalités avancées.
- **Rôles** :
  - **Utilisateur** : Accès aux fonctionnalités de base.
  - **Cheffe d’équipe** : Gestion des membres, des collections et des tables de correspondance pour son équipe.
  - **Administratrice** : Publication de templates/collections, gestion des utilisateurs, et validation des demandes de publication.

### 5. **Gestion d’Équipe**
Accessible dans la page profile
- **Création d’équipes** : Tout utilisateur peut créer une équipe et en devenir cheffe.
- **Gestion des membres** : Ajout/retrait de membres, partage de collections et tables de correspondance au sein de l’équipe.

---

## Fonctionnalités Optionnelles (Avancées)

- **Transfert de propriété d’équipe** : Permettre à une cheffe d’équipe de transférer son rôle.


---

## Bases de Données Externes Envisagées

1. **NCBI (GenBank)** : Pour accéder aux séquences et annotations détaillées des plasmides.
2. **Addgene** : Pour les informations sur les plasmides partagés par la communauté scientifique.
3. **UniProt** : Pour les annotations protéiques liées aux séquences codantes.
4. **REBASE** : Pour les informations sur les sites de restriction et enzymes.

---

## Organisation du Projet

- **Branches** (à regarder pour l'instant):
  - `MAQUETTE` : Contient les maquettes des interfaces utilisateur.
  - `ANGE` : Développement des fonctionnalités back-end et intégration.
  - `AGASH` : Bonne intégration des bases de données (voir le fichier DIAGRAMME_UML.pdf)
- **Outils** :
  - **Django** : Framework principal pour le back-end et la gestion des utilisateurs.
  - **Bootstrap** : Pour les interfaces utilisateur.
  - **Biopython** : Pour la manipulation des fichiers GenBank et les analyses de séquences.
  - **GitHub** : Versionnement et gestion des issues.

