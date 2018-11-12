const ledId = [
    'LLIV',
    'LKIT',
    'LBED',
    'LBAT'
];

ledId.forEach(
    led => {
        $(`#${led}`).on('click',
            function(){
                console.log('send',$(this).prop('checked'));
                socket.send(
                    JSON.stringify({
                        type : 'LED CONTROL',
                        id : led,
                        state : $(this).prop('checked'),
                        update : false
                    })
                );
            })

    }
);