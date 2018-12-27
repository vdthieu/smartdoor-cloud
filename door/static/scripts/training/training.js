$('#train_button').on('click',
    function () {
        socket.send(
            JSON.stringify({
                type: 'TRAINING CONTROL',
                state: true
            })
        );
    });

function updateTrainingSummary(data) {
    $('#row-count').text(data.row_count);
    const created_date = new Date(data.created_at);
    const created_at =
        (created_date.getHours() > 10 ? created_date.getHours().toString() : `0${created_date.getHours()}`) + ':' +
        (created_date.getMinutes() > 10 ? created_date.getMinutes().toString() : `0${created_date.getMinutes()}`) + ' ' +
        (created_date.getDate() > 10 ? created_date.getDate().toString() : `0${created_date.getDate()}`) + '/' +
        (created_date.getMonth() > 9 ? (created_date.getMonth() + 1).toString() : `0${created_date.getMonth() + 1 }`) + '/' +
        created_date.getFullYear();
    $('#latest-training').text(created_at);

    const accuracy = data.devices.map(
        item => item.type === 'C' ?
            `<div>${item.device_name}:A(${item.accuracy})</div>`
            :
            `<div>${item.device_name}:MSE(${item.mean_squared_error})</div>`
    ).join('');
    $('#accuracy').html(accuracy);
    $('#training-time').text(`${data.train_time.toFixed(2)}s`);
}