const $ = jQuery.noConflict();
let socket = new WebSocket('ws://' + window.location.host + '/ws/door/');

socket.addEventListener('open', function (event) {
    console.log('kết nối thành công');
    getTable();
});

socket.onmessage = function (e) {
    let data = JSON.parse(e.data);
    console.log(data);
    switch (data.type) {
        case 'DATA TABLE': {
            appendDataTable(data.data);
            break;
        }
        case 'UNSHIFT DATA TABLE':{
            unshiftDataTable(data);
            break;
        }
        case 'TRAINING SUMMARY':{
            updateTrainingSummary(data.data);
            $('#train_button').html('Start!');
            break;
        }
        case 'PREDICTION STATE': {
            $('#predict_button').prop('checked',data.value);
            break;
        }
        case 'TRAINING STATUS' : {
            updateTrainingStatus(data);
            break;
        }

    }
};
