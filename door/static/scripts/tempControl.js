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

let slider = document.getElementById("TOFF");
let output = document.getElementById("light");
output.innerHTML = slider.value; // Display the default slider value
// Update the current slider value (each time you drag the slider handle)
slider.oninput = function () {
    output.innerHTML = this.value;
};

let slider2 = document.getElementById("THOM");
let output2 = document.getElementById("temp");
output.innerHTML = slider.value; // Display the default slider value
// Update the current slider value (each time you drag the slider handle)
slider2.oninput = function () {
    output2.innerHTML = this.value;
};