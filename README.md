Spelling Bee Practice
==============
Nikita Ustiuzhanin

Final project for CS50x 2020

----------------------------
_Overview:_

First you need to register. Then you start from choose a difficulty level: Beginner, Intermediate and Advanced. Use "Spell a word" button for hearing the word. Need to enter it correctly and press "Try". You will see result and it will be added in your profile statistic. You can check it on "Profile" page. If you were incorrect you can use "Hint". The word will change to next after correct input.

Tried to make all logic on one page without reloading using JavaScript. Statistic saving in SQL database for every user. Flask framework as base. Bootstrap for templates.

----------------------------
_If you want to run it locally:_

Go to project directory.

Create virtual environment.

Run Command:

	python pip install -r requirements.txt
	
	flask run
