# team-online-tactics
A game for the mandatory assignment in INF142 Spring 2022.

Based upon the now antiquated team-local-tactics, but converted to work over networks. The basic concept is suspiciously alike a game with a similar name, but this is a simpler rock-paper-scissors-esque implementation that plays in the terminal. 

## Prerequisites
* python (3.10.2 recommended)
* rich

## Usage
In separate terminals, in order:
``` 
python3 database.py
python3 server.py 
python3 client.py
python3 client.py 
```
Client.py must be run in two instances, one for each player.

* The clients will automatically connect and be assigned an ID.
* If you select 'Play', please do so on both clients before Player 1 selects their first champion.
* Both champions select their champions in order. When Player 1 is done picking three champions, he starts waiting for the match results.
* At this point, Player 2 is left hanging waiting for its turn. 
  * I guess the server doesn't tell P2 it's their turn. I'm not entirely sure why.
  * **In the Player 2 client, you might have to ctrl+c out of the waiting loop to pick the last champion, if it hangs.**
* If you want to patch champions live, edit the some_champs.txt file. It's loaded every round.

If a client disconnects or crashes, the server has to be restarted. I didn't implement a way for the server to clear up player slots in time.

## Playing
* The client will automatically attempt to connect to the server, and present a list of commands if successful.
* Each player picks their respective champions, and the game plays itself.
* Results are presented to both the clients

## Implementation
* The game consist, in addition to the core gameplay code, of three separate scripts:
  * server.py - handles communication to clients and database
  * database.py - responsible for updating and fetching database
  * client.py - takes input and shows results to players
* The three scripts communicate through TCP using sockets. 
* Pickle is used for converting data into a byte stream before sending over the TCP connection.

## Authors
* **Viljar Slettli - Group 99**
* [**Daniel (Instructor)**](https://github.com/daniel-heres) - Base code from team-local-tactics

## Note to TA's

### Bugs
* The server doesn't automatically free up a 'player slot' if a client abruptly disconnects
* Clients don't always handle the server abruptly crashing well
* Crash if P1 picks a champion before P2 is in the 'waiting for turn' state
* Right before handing in the assignment, I introduced a bug where clients can no longer properly shut down the server. 
  * The client that makes the request and the database shuts down, but not the server or the other client.
  * The server doesn't break its loop or close the sockets and selectors properly.

### Current progress
#### Server
* Server and client can communicate
* Server handles player teams and sends to client
* Server sends champion list to client
* Server handles playing out match, returns match object to client
#### Client
* Client offers command menu to interact with server
  * Play, reset teams, shut down etc.
* Client takes champion selection input and forwards to server
* Client can request and print match history
* Separate player clients
* Game can be 'played'
#### Datbase
* Database transmits champions to Server through sockets
* Database stores match history (server>database)
