const ledId = [
    'LLIV',
    'LKIT',
    'LBED',
    'LBAT'
];

ledId.forEach(
    led => {
        $(`#${led}`).on('click',
            function () {
                console.log('send',{
                        type: 'LED CONTROL',
                        id: led,
                        state: $(this).prop('checked'),
                        update: false
                    });
                socket.send(
                    JSON.stringify({
                        type: 'LED CONTROL',
                        id: led,
                        state: $(this).prop('checked'),
                        update: false
                    })
                );
            })
    }
);