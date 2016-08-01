

class Master(object):
    def __init__(self, container):
        self.container = container

    def create_game(self, owner_username):
        return self.container.create_game(owner_username)

    def join_game(self, username, game_id):
        # simplest way, call start_room always
        # call script.start_room
        room_id = 'room1'
        player = findAndModify(
            query:{game_id: game_id, username: username},
            update:$setOnInsert:{room_id:room_id},
                   $set:{token: new_token()},
            upsert: true,
            new: true,
        )

        # create/upsert room
        db.rooms.findAndModify({
            query:{'game_id':'games_0'},
            update:{
                $set:{'requested':true},
                $setOnInsert:{'active': false,'node_name':null}},
            upsert:true,
            new:true}
        )

        #  state: initial - script player create on node
        # to create a room
        # check room exists, if not, create
        self.container.dbase.save_object({'state': {}, 'room_id': '1', 'game_id': game_id}, 'rooms')
