$('#train_switch').on('click',
            function(){
                socket.send(
                    JSON.stringify({
                        type : 'TRAINING CONTROL',
                        state : $(this).prop('checked'),
                        update : false
                    })
                );
            });