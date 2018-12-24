$('#train_button').on('click',
            function(){
                socket.send(
                    JSON.stringify({
                        type : 'TRAINING CONTROL',
                        state : true
                    })
                );
            });