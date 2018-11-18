const $ = jQuery.noConflict();
let socket = new WebSocket('ws://' + window.location.host + '/ws/door/');

socket.addEventListener('open', function (event) {
    console.log('kết nối thành công');

});

socket.onmessage = function (e) {
    let data = JSON.parse(e.data);
    console.log(data);
    switch (data.type) {
        case 'LED CONTROL':
            if(ledId.some( item => item === data.id)){
                $(`#${data.id}`).prop('checked',data.state)
            }
            break;
        case 'TEMP CONTROL':
            if(tempIds.some(item => item === data.id)){
                $(`#${data.id}`).val(data.state)
            }
            break
        case 'DEVICE STATUS':
            data.device_status.forEach(
                item => {
                    console.log('update',item);
                    if(item.status){
                        updateStatusBar(item.id,'info',"Đang hoạt động")
                    }else{
                        updateStatusBar(item.id,'danger','Không có kết nối')
                    }
                }
            )
    }
};

const device_tag_dict= {
    SERVO : [
        'device_servo_container',
        jQuery('#device_servo_label'),
        jQuery('#device_servo_content')
    ],
    LIGHT : [
        'device_light_container',
        jQuery('#device_light_label'),
        jQuery('#device_light_content')
    ],
    RFID : [
        'device_rfid_container',
        jQuery('#device_rfid_label'),
        jQuery('#device_rfid_content')
    ]
};

function updateStatusBar(device, state, message) {
    //state : ['info', 'danger','success']
    console.log(device)
    const [containerId, label, content] = device_tag_dict[device];
    const container = jQuery('#' + containerId);
    const element = document.getElementById(containerId);
    const elementClasses = element.className.split(' ');

    elementClasses.forEach(function (value) {
        if (value.substring(0, 5) === 'alert' && value !== 'alert') {
            container.toggleClass(value);
            container.toggleClass('alert-' + state);
            label.toggleClass('badge' + value.substring(5, value.length));
            label.toggleClass('badge-' + state);
        }
    });
    content.text(message);
}