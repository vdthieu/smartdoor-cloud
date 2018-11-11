let $ = jQuery.noConflict();
let iconDoor = jQuery("#door_status_icon "); // hình cửa
let icnControlDoor = jQuery("#door_control_icon "); // thẻ bao icon cửa
let btnControlDoor = jQuery('#door_control_btn'); // nút đóng cửa
let btnAutoDoor = jQuery('#door_auto_btn');  // nút tự động
let btnSavePwd = jQuery("#save_pwd_btn "); // nút lưu password
let pwdTable = jQuery('#password-table > tbody:last-child');
let htyTable = jQuery('#history-table > tbody > tr:first');
let statusContainer = jQuery('#status-container');
let statusBar = jQuery('#status');
let statusLabel = jQuery('#status-label');
let statusContent = jQuery('#status-content');
let localPwd = jQuery('#door-local-pwd');
let btnSaveLocalPwd = jQuery('#save-local-pwd');
let dataPwd = jQuery("#door_pwd ");
let dataPwdType = jQuery("#door_type ");
let dataNote = jQuery('#door_note');
let dataApplyDate = jQuery("#door_apply_date ");
let dataDueDate = jQuery("#door_due_date ");
let pwdTiming = jQuery('#timing');

let doorOpenStatus = false;
let displayDay = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

let socket = new WebSocket('ws://' + window.location.host + '/ws/door/');

function updateDoorIcon() {
    if (doorOpenStatus) {
        iconDoor.attr('src', "{% static 'door-open.png' %} ");
        btnControlDoor.text("Mở ");
        btnControlDoor.addClass('btn-primary');
        btnControlDoor.removeClass('btn-light');
    } else {
        iconDoor.attr('src', "{% static 'door-close.png' %} ");
        btnControlDoor.text("Đóng ");
        btnControlDoor.removeClass('btn-primary');
        btnControlDoor.addClass('btn-light');
    }
}

let slider = document.getElementById("LightRange");
let output = document.getElementById("light");
output.innerHTML = slider.value; // Display the default slider value
// Update the current slider value (each time you drag the slider handle)
slider.oninput = function () {
    output.innerHTML = this.value;
}

let slider2 = document.getElementById("TempRange");
let output2 = document.getElementById("temp");
output.innerHTML = slider.value; // Display the default slider value
// Update the current slider value (each time you drag the slider handle)
slider2.oninput = function () {
    output2.innerHTML = this.value;
};

function updateDoorAuto() {
    if (isAuto) {
        btnAutoDoor.removeClass(' btn-light');
        btnAutoDoor.addClass('btn-primary ');
        btnAutoDoor.text('Tự động')
    } else {
        btnAutoDoor.addClass(' btn-light');
        btnAutoDoor.removeClass('btn-primary ');
        btnAutoDoor.text('Thủ công')
    }
}

function dateToString(_date) {
    if (_date.length === 0) return " ";
    if (typeof _date === 'string') _date = new Date(_date);
    let day = displayDay[_date.getDay()];
    let date = (_date.getDate() > 9) ? _date.getDate() : ('0' + _date.getDate());
    let month = ((_date.getMonth() + 1) > 9) ? (_date.getMonth() + 1) : ('0' + (_date.getMonth() + 1));
    let year = _date.getFullYear();
    let hour = (_date.getHours() > 9) ? _date.getHours() : ('0' + _date.getHours());
    let minutes = (_date.getMinutes() > 9) ? _date.getMinutes() : ('0' + _date.getMinutes());
    return day + ' ' + date + '/' + month + '/' + year + ' - ' + hour + ':' + minutes
}

// devices status tag
let statusServoContainer = 'device_servo_container'
let statusServoLabel = jQuery('#device_servo_label');
let statusServoContent = jQuery('#device_servo_content');

let statusKeypadContainer = 'device_keypad_container'
let statusKeypadLabel = jQuery('#device_keypad_label');
let statusKeypadContent = jQuery('#device_keypad_content');

let statusRfidContainer = 'device_rfid_container';
let statusRfidLabel = jQuery('#device_rfid_label');
let statusRfidContent = jQuery('#device_rfid_content');

function updateStatusBar(device, state, message) {
    let containerId, label, content;
    switch (device) {
        case 'servo':
            [containerId, label, content] = [statusServoContainer, statusServoLabel, statusServoContent];
            break;
        case 'keypad':
            [containerId, label, content] = [statusKeypadContainer, statusKeypadLabel, statusKeypadContent];
            break;
        case 'rfid':
            [containerId, label, content] = [statusRfidContainer, statusRfidLabel, statusRfidContent];
            break;
    }
    let container = jQuery('#' + containerId);
    let element = document.getElementById(containerId);
    let elementClasses = element.className.split(' ');
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

function deletePwd(password) {
    socket.send(JSON.stringify({
        delete_password: password
    }))
}

socket.addEventListener('open', function (event) {
    updateStatusBar('success', 'Kết nối đến server thành công')
});

socket.onmessage = function (e) {
    let data = JSON.parse(e.data);
    // update door status
    if (data.hasOwnProperty('door_status')) {
        let message = data['door_status'];
        if (message === 'close') {
            doorOpenStatus = false;
        }
        if (message === 'open') {
            doorOpenStatus = true;
        }
        updateDoorIcon();
        return;
    }
    // update password table
    if (data.hasOwnProperty('add_pwd_list')) {
        let dataContent = data['add_pwd_list'];
        if (dataContent.ok) {
            let value =
                '<tr> ' +
                '<td>' + dataContent.pwd + '</td>' +
                '<td>' + (dataContent.type ? 'Tạm thời' : 'Cố định') + '</td>' +
                '<td>' + dateToString(dataContent.create) + '</td>' +
                '<td>' + dateToString(dataContent.apply) + '</td>' +
                '<td>' + dateToString(dataContent.due) + '</td>' +
                '<td>' + dataContent.note + '</td>' +
                '<td>' +
                '<button onclick="deletePwd( ' + "' " + dataContent.pwd + " '" + ') ">' +
                '<i class="fa fa-trash-o "></i>' +
                '</button>' +
                '</td>' +
                '</tr>';
            pwdTable.append(value);
            dataPwd.val('');
            if (dataPwdType.is(':checked')) {
                dataPwdType.attr('checked', false);
                pwdTiming.toggle();
            }
            dataNote.val('');
            dataApplyDate.val('');
            dataDueDate.val('');
        } else {
            alert(dataContent.message)
        }
        btnSavePwd.removeAttr('disabled');
        return;
    }
    if (data.hasOwnProperty('remove_pwd_list')) {
        let password = data.remove_pwd_list;
        let row = jQuery('#password-table > tbody >tr :contains(' + password + ')');
        row.parent().remove();
        return;
    }
    // update history table
    if (data.hasOwnProperty('update_hty_list')) {
        let dataContent = data['update_hty_list'];
        let value =
            '<tr> ' +
            '<td>' + dataContent.action + '</td>' +
            '<td>' + dateToString(dataContent.time) + '</td>' +
            '</tr>';
        htyTable.before(value);
        return;
    }
    // update active device
    if (data.hasOwnProperty('update_devices_status')) {
        let dataContent = data['update_devices_status'];
        if (dataContent.servo) {
            updateStatusBar('servo', 'info', 'Đang hoạt động')
        } else {
            updateStatusBar('servo', 'danger', 'Không có kết nối')
        }
        if (dataContent.keypad) {
            updateStatusBar('keypad', 'info', 'Đang hoạt động')
        } else {
            updateStatusBar('keypad', 'danger', 'Không có kết nối')
        }
        if (dataContent.rfid) {
            updateStatusBar('rfid', 'info', 'Đang hoạt động')
        } else {
            updateStatusBar('rfid', 'danger', 'Không có kết nối')
        }
        return;
    }
    // update door auto status
    if (data.hasOwnProperty('update_door_auto')) {
        isAuto = data.update_door_auto === 'on';
        updateDoorAuto()
    }
};

icnControlDoor.click(function () {
    let data;
    if (!doorOpenStatus)
        data = {door_control: 'open'};
    else data = {door_control: 'close'};
    socket.send(JSON.stringify(data));
});

btnControlDoor.click(function () {
    let data;
    if (!doorOpenStatus)
        data = {door_control: 'open'};
    else data = {door_control: 'close'};
    socket.send(JSON.stringify(data));
});

btnSavePwd.click(function () {
    let data = {
        door_save_pwd: {
            pwd: dataPwd.val(),
            type: dataPwdType.is(':checked'),
            note: dataNote.val(),
            create: new Date(),
            apply: dataApplyDate.val(),
            due: dataDueDate.val()
        }
    };
    socket.send(JSON.stringify(data));
    btnSavePwd.attr('disable', true)
});

btnSaveLocalPwd.click(function () {
    socket.send(JSON.stringify({
        local_pwd: localPwd.val()
    }));
    localPwd.val('')
});

btnAutoDoor.click(function () {
    socket.send(JSON.stringify({
        door_auto: !isAuto ? 'on' : 'off'
    }))
});


socket.onclose = function (e) {
    updateStatusBar('danger', 'Mất kết nối đến server')
};
jQuery('#close-action').on("click ", function () {
    socket.send(JSON.stringify({
        message: 'close'
    }))
});
jQuery('#open-action').on("click ", function () {
    socket.send(JSON.stringify({
        message: 'open'
    }))
});
