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