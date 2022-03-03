# team-online-tactics
A game for the mandatory assignment in INF142 Spring 2022.

Based upon the now antiquated team-local-tactics, but converted to work over networks. The basic concept is suspiciously alike a game with a similar name, but this is a simpler rock-paper-scissors-esque implementation that plays in the terminal. 

## Prerequisites
* python (3.10.2 recommended)
* rich

## Usage
In separate terminals:
``` 
python3 server.py 
python3 database.py
python3 client.py 
```
Client.py must be run in two instances, one for each player.

## Playing
* The client will automatically attempt to connect to the server, and present a list of commands if successful.
* Each player picks their respective champions, and the game plays itself.
* Results are presented

## Implementation
* The game (will) consist, in addition to the core gameplay code, of three separate scripts:
  * server.py - server script, handles communication between clients and database
  * client.py - client (player) script, takes input and outputs results to players
  * database.py - script responsible for updating and fetching database
* The three above mentioned scripts communice through TCP using sockets. 
* Pickle is used for converting data into a byte stream before sending over the TCP connection.

## Authors
* **Viljar Slettli - Group 99**
* [**Daniel**](https://github.com/daniel-heres) - Base code from team-local-tactics

## Note to TA's
This readme will probably change as I add more features and figure out the inner workings of the complete assignment. Not everything here is true at the moment, like running client.py in separate terminals. That doesn't work yet.
