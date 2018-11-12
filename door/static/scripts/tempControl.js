const tempIds = [
    'TOFF',
    'THOM'
];

tempIds.forEach(
    tempId => {
        $(`#${tempId}`).on('change',
            function () {
                socket.send(
                    JSON.stringify({
                        type : 'TEMP CONTROL',
                        id : tempId,
                        state : $(this).val(),
                        update : false
                    })
                );
            })
    }
);