
var index = {};

index.games = [];


function reloadgames() {
    net.perform_get("/games",
        function(data){
            index.games = data;
            turtlegui.reload();
        },
        function(errTxt, jqXHR){ alert("Error loading games: "+JSON.stringify(errTxt));});
}

function create_game() {
    net.perform_post('/creategame', {},
        function(){ reloadgames();},
        function(errTxt, jqXHR){ alert("Error creating game: "+JSON.stringify(errTxt));});
}

function join_game(game) {
    net.perform_post('/join/' + game.game_id, {},
        function(data){
            window.location.href = '/play/' + game.game_id;
            //= "http://" + data['node_name'] + "/rooms/play/" + game.game_id;
            // check data for room link
            // redirect to node 
        },
        function(errTxt, jqXHR){ alert("Error joining game: "+JSON.stringify(errTxt));});
}


$(document).ready(function() {
console.log("initing");
    turtlegui.reload()
    reloadgames();
});

