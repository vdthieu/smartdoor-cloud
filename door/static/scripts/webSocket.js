const socket = new WebSocket('ws://' + window.location.host + '/ws/door/');


socket.addEventListener('open', function (event) {
    console.log('kết nối thành công')
});

socket.onmessage = function (e) {
    let data = JSON.parse(e.data);
    console.log(data)
    switch (data.type) {
        case 'LED CONTROL':
            if(ledId.some( item => item === data.id)){
                $(`#${data.id}`).prop('checked',data.state)
            }
    }
};
