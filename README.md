# ESP32 IDE — Hackers Tchad Edition

> Un environnement de développement graphique avancé pour microcontrôleurs ESP32, conçu pour détecter automatiquement les cartes ESP32 branchées, envoyer du code MicroPython, gérer les fichiers, surveiller les ports série, et offrir une expérience proche d’un IDE professionnel.

---

## Table des matières

1. [Présentation](#présentation)
2. [Fonctionnalités principales](#fonctionnalités-principales)
3. [Captures et aperçu](#captures-et-apercu)
4. [Installation](#installation)
5. [Utilisation](#utilisation)
6. [Détection automatique de l’ESP32](#détection-automatique-de-lesp32)
7. [Exécution du code sur l’ESP32](#exécution-du-code-sur-lesp32)
8. [Gestionnaire de fichiers](#gestionnaire-de-fichiers)
9. [Terminal série](#terminal-série)
10. [Éditeur de code](#éditeur-de-code)
11. [Configuration](#configuration)
12. [Raccourcis clavier](#raccourcis-clavier)
13. [Dépannage](#dépannage)
14. [Sécurité](#sécurité)
15. [Ressources et documentation](#ressources-et-documentation)
16. [Applications recommandées](#applications-recommandées)
17. [Livres recommandés](#livres-recommandés)
18. [Liens utiles](#liens-utiles)
19. [Contribuer](#contribuer)
20. [Licence](#licence)
21. [Auteur](#auteur)

---

## Présentation

Ce projet est un IDE autonome écrit en Python avec Tkinter. Il permet de développer, tester et déployer des programmes sur des cartes ESP32 sans passer par une ligne de commande complexe. L’interface est pensée pour être claire, rapide et accessible aux débutants comme aux utilisateurs avancés.

L’objectif est de fournir un outil qui :

- Détecte automatiquement les ESP32 branchés en USB ;
- Permet d’éditer du code avec coloration syntaxique ;
- Envoie le code vers l’ESP32 en un clic ;
- Affiche les retours du port série en temps réel ;
- Gère les fichiers présents sur l’ESP32 ;
- Offre des options de configuration avancées.

Ce logiciel fonctionne sur Linux, Windows et macOS.

---

## Fonctionnalités principales

### Détection automatique

L’application surveille en permanence les ports USB. Dès qu’un ESP32 est branché, il apparaît dans la liste des appareils disponibles. Si un seul appareil est détecté, il peut être sélectionné automatiquement selon les préférences de l’utilisateur.

### Éditeur de code intégré

L’éditeur supporte :

- La coloration syntaxique pour MicroPython et Python ;
- La numérotation des lignes ;
- La gestion des indentations ;
- La recherche et le remplacement ;
- La gestion de plusieurs onglets ;
- L’annulation et le rétablissement ;
- L’affichage des caractères invisibles en option.

### Envoi du code vers l’ESP32

Le code peut être exécuté de plusieurs manières :

- Exécution immédiate du script dans la console REPL ;
- Téléversement du fichier sur le système de fichiers de l’ESP32 ;
- Exécution d’un fichier présent sur l’ESP32 ;
- Réinitialisation de la carte après envoi.

### Terminal série

Un terminal intégré affiche les messages envoyés par l’ESP32. Il permet d’envoyer des commandes manuellement au REPL, de copier les messages, de les sauvegarder dans un fichier et de configurer la vitesse de communication.

### Gestionnaire de fichiers

L’explorateur de fichiers permet de :

- Voir les fichiers présents sur l’ESP32 ;
- Supprimer des fichiers ;
- Renommer des fichiers ;
- Créer de nouveaux fichiers ou répertoires ;
- Télécharger des fichiers depuis l’ESP32 vers l’ordinateur ;
- Envoyer des fichiers depuis l’ordinateur vers l’ESP32.

### Outils complémentaires

- Vérificateur de syntaxe ;
- Formatage automatique du code ;
- Générateur de squelettes de projet ;
- Gestion des préférences utilisateur ;
- Thèmes clair et sombre ;
- Sauvegarde automatique ;
- Historique des commandes du terminal ;
- Support du glisser-déposer pour ouvrir des fichiers.

---

## Captures et aperçu

L’interface se compose de plusieurs zones principales :

1. Barre de menu en haut avec accès aux fonctions principales.
2. Barre d’outils avec les actions rapides.
3. Panneau latéral gauche avec l’explorateur de fichiers et la liste des ports.
4. Zone centrale avec l’éditeur de code à onglets.
5. Panneau inférieur avec le terminal série et les journaux.

L’interface est entièrement redimensionnable. Les panneaux peuvent être masqués ou affichés selon les besoins.

---

## Installation

### Prérequis

- Python 3.10 ou supérieur
- pip
- Un câble USB compatible avec la carte ESP32
- Les pilotes USB adaptés au chipset de votre carte :
  - CP2102 / CP2104 : Silicon Labs
  - CH340 / CH341 : WCH
  - FTDI : FTDI

### Étapes

1. Cloner ou télécharger le dépôt :

```bash
git clone https://github.com/hackers-tchad/esp32-ide.git
cd esp32-ide
```

2. Créer un environnement virtuel :

```bash
python -m venv venv
```

3. Activer l’environnement virtuel :

Sur Linux ou macOS :

```bash
source venv/bin/activate
```

Sur Windows :

```bash
venv\Scripts\activate
```

4. Installer les dépendances :

```bash
pip install -r requirements.txt
```

5. Lancer l’application :

```bash
python esp32_ide_hackers_tchad.py
```

---

## Utilisation

### Premier lancement

Au premier démarrage, l’application affiche une fenêtre de bienvenue. L’utilisateur peut configurer :

- Le thème par défaut ;
- Le port de communication préféré ;
- La vitesse de transmission ;
- Le dossier de projets par défaut.

### Créer un nouveau fichier

Cliquez sur Fichier > Nouveau ou utilisez le raccourci Ctrl+N. Un nouvel onglet s’ouvre dans l’éditeur.

### Ouvrir un fichier existant

Cliquez sur Fichier > Ouvrir ou utilisez Ctrl+O. Vous pouvez aussi glisser-déposer un fichier dans la fenêtre.

### Enregistrer un fichier

Cliquez sur Fichier > Enregistrer ou utilisez Ctrl+S.

### Connecter un ESP32

Branchez la carte ESP32 à l’ordinateur. L’application détecte automatiquement le port. Sélectionnez le port dans la liste déroulante, puis cliquez sur Connecter.

---

## Détection automatique de l’ESP32

L’application analyse les ports série disponibles et identifie ceux correspondant à un ESP32. La reconnaissance s’appuie sur :

- Le nom du port ;
- Le VID et le PID du périphérique USB ;
- La description matérielle ;
- Le fabricant déclaré.

Les identifiants reconnus incluent notamment :

- Espressif Systems
- Silicon Labs CP210x
- WCH CH340 / CH341
- FTDI FT232

La détection est réactive : dès qu’une carte est branchée ou débranchée, l’interface se met à jour.

---

## Exécution du code sur l’ESP32

### Mode immédiat

Le contenu de l’éditeur est envoyé ligne par ligne au REPL MicroPython. Ce mode est idéal pour tester rapidement des commandes.

### Mode téléversement

Le fichier est envoyé sur le système de fichiers de l’ESP32. Vous pouvez ensuite l’exécuter ou le définir comme fichier principal.

### Mode main.py

Le fichier est téléversé sous le nom `main.py` et la carte est redémarrée. Le programme démarre automatiquement.

### Mode boot.py

Le fichier est téléversé sous le nom `boot.py`. Il sera exécuté à chaque démarrage de la carte.

---

## Gestionnaire de fichiers

Le panneau de fichiers affiche l’arborescence de l’ESP32. Pour chaque fichier, vous pouvez :

- L’ouvrir dans l’éditeur ;
- Le renommer ;
- Le supprimer ;
- Le télécharger sur l’ordinateur.

Vous pouvez aussi créer un nouveau répertoire ou un nouveau fichier directement depuis l’interface.

---

## Terminal série

Le terminal affiche en temps réel les données reçues depuis l’ESP32. Il supporte :

- L’envoi de commandes au REPL ;
- L’historique des commandes avec les flèches haut et bas ;
- La copie du contenu affiché ;
- La sauvegarde du journal dans un fichier texte ;
- L’effacement de l’affichage ;
- Le réglage de la vitesse, du nombre de bits, de la parité et des bits d’arrêt.

---

## Éditeur de code

L’éditeur intégré propose les fonctionnalités suivantes :

- Coloration syntaxique personnalisable ;
- Numérotation des lignes ;
- Surlignage de la ligne active ;
- Repli de code basique ;
- Complétion automatique simple ;
- Détection des erreurs de syntaxe ;
- Indentation automatique ;
- Conversion des tabulations en espaces.

Les mots-clés reconnus incluent ceux de Python et de MicroPython, ainsi que les modules courants comme `machine`, `network`, `urequests`, `ujson`, `utime`, etc.

---

## Configuration

Les préférences sont stockées dans un fichier JSON dans le dossier utilisateur. Elles incluent :

- Thème de l’interface ;
- Police et taille de l’éditeur ;
- Paramètres du port série ;
- Dossier de projets par défaut ;
- Options de sauvegarde automatique ;
- Identifiants Wi-Fi par défaut ;
- Préférences de détection automatique.

Vous pouvez exporter et importer vos préférences depuis le menu Outils.

---

## Raccourcis clavier

| Action | Raccourci |
|--------|-----------|
| Nouveau fichier | Ctrl+N |
| Ouvrir un fichier | Ctrl+O |
| Enregistrer | Ctrl+S |
| Enregistrer sous | Ctrl+Shift+S |
| Couper | Ctrl+X |
| Copier | Ctrl+C |
| Coller | Ctrl+V |
| Annuler | Ctrl+Z |
| Rétablir | Ctrl+Y |
| Rechercher | Ctrl+F |
| Remplacer | Ctrl+H |
| Exécuter sur ESP32 | F5 |
| Téléverser sur ESP32 | F6 |
| Réinitialiser l’ESP32 | F7 |
| Connecter / déconnecter | F8 |
| Vérifier la syntaxe | F9 |
| Ouvrir les préférences | Ctrl+, |
| Quitter | Ctrl+Q |

---

## Dépannage

### L’ESP32 n’apparaît pas dans la liste

- Vérifiez que le câble USB supporte le transfert de données.
- Installez les pilotes du chipset USB.
- Sur Linux, ajoutez votre utilisateur au groupe `dialout` ou `uucp`.
- Essayez un autre port USB.

### Le téléversement échoue

- Assurez-vous que la carte est bien connectée.
- Vérifiez que le bon port est sélectionné.
- Fermez les autres programmes utilisant le port série.
- Vérifiez que le fichier ne contient pas d’erreur de syntaxe.

### Le terminal ne reçoit rien

- Vérifiez la vitesse de communication.
- Redémarrez la carte.
- Vérifiez que le programme sur l’ESP32 envoie bien des messages.

### L’application ne démarre pas

- Vérifiez votre version de Python.
- Installez les dépendances avec `pip install -r requirements.txt`.
- Consultez le fichier de log dans le dossier utilisateur.

---

## Sécurité

- Ne téléversez jamais de code provenant d’une source non fiable.
- Faites attention lors de l’utilisation de commandes qui effacent la mémoire flash.
- Sauvegardez vos projets avant de flasher une nouvelle image MicroPython.
- L’application n’envoie aucune donnée sur Internet par défaut.

---

## Ressources et documentation

### Documentation officielle MicroPython

- https://docs.micropython.org

### Documentation ESP32

- https://docs.espressif.com/projects/esp-idf/en/latest/esp32/

### Documentation Python

- https://docs.python.org/3/

### Documentation Tkinter

- https://docs.python.org/3/library/tkinter.html

### Documentation pySerial

- https://pyserial.readthedocs.io

### Documentation esptool

- https://docs.espressif.com/projects/esptool/en/latest/

---

## Applications recommandées

- **Thonny** : IDE léger avec support MicroPython intégré.
- **Mu Editor** : IDE pédagogique pour microcontrôleurs.
- **VS Code** : éditeur extensible avec extensions MicroPython et Serial.
- **PuTTY** : client terminal pour port série.
- **mpfshell** : shell interactif pour système de fichiers MicroPython.
- **rshell** : shell à distance pour MicroPython.
- **ampy** : outil en ligne de commande pour gérer les fichiers MicroPython.
- **PlatformIO** : plateforme de développement embarqué.

---

## Livres recommandés

- *Programming Microcontrollers with Python* par Armstrong Subero
- *MicroPython for the Internet of Things* par Charles Bell
- *Python for Microcontrollers* par Donald Norris
- *The Definitive Guide to ARM Cortex-M3 and Cortex-M4 Processors* par Joseph Yiu
- *Embedded Systems Architecture* par Tammy Noergaard
- *Building Wireless Sensor Networks* par Robert Faludi
- *Make: Python Programming for Beginners* par Bob Dukish
- *Programming Arduino* par Simon Monk
- *The Hardware Hacking Handbook* par Jasper van Woudenberg et Colin O’Flynn
- *Practical IoT Hacking* par Fotios Chantzis et al.
- *Hacking Electronics* par Simon Monk
- *The Art of Electronics* par Paul Horowitz et Winfield Hill
- *Learning Python* par Mark Lutz
- *Fluent Python* par Luciano Ramalho
- *Python Cookbook* par David Beazley et Brian K. Jones

---

## Liens utiles

- https://micropython.org/download/?board=generic_esp32
- https://github.com/micropython/micropython
- https://github.com/espressif/esptool
- https://www.espressif.com/en/products/socs/esp32
- https://www.python.org
- https://pypi.org
- https://hackaday.io
- https://www.instructables.com
- https://learn.sparkfun.com
- https://learn.adafruit.com
- https://randomnerdtutorials.com
- https://docs.wemos.cc
- https://github.com/hackers-tchad

---

## Contribuer

Les contributions sont les bienvenues. Vous pouvez :

- Signaler des bogues ;
- Proposer des améliorations ;
- Soumettre des correctifs ;
- Partager des exemples de projets.

Pour contribuer au code, forkez le dépôt, créez une branche et soumettez une pull request.

---

## Licence

Ce projet est distribué sous licence MIT. Vous êtes libre de l’utiliser, de le modifier et de le redistribuer. L’auteur ne peut être tenu responsable des dommages causés par une utilisation incorrecte du logiciel.

---

## Auteur

**Hackers Tchad**

- Année : 2026
- Pays : Tchad
- Communauté : hackers-tchad
- Projet : ESP32 IDE avancé

Ce projet a été développé pour simplifier l’accès au développement embarqué et encourager l’apprentissage de la programmation sur microcontrôleurs au Tchad et partout ailleurs.

---

## Historique des versions

- 2026.1.0 : Première version publique
  - Détection automatique des ESP32
  - Éditeur avec coloration syntaxique
  - Terminal série intégré
  - Gestionnaire de fichiers
  - Thèmes clair et sombre
  - Préférences utilisateur
  - Support multiplateforme

---

## Remerciements

Merci à toutes les personnes et communautés qui contribuent à rendre la technologie accessible :

- L’équipe MicroPython
- L’équipe Espressif
- Les contributeurs de pySerial
- Les membres de la communauté Hackers Tchad
- Tous les makers et développeurs du monde entier

---

## Notes finales

Ce README fournit une vue d’ensemble complète de l’application. Pour plus de détails, consultez les commentaires dans le code source et les fichiers d’aide intégrés à l’interface.

Bonne programmation avec votre ESP32 !
