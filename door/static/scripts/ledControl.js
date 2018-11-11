const $ = jQuery.noConflict();
const ledId = [
    'LLIV',
    'LKIT',
    'LBED',
    'LBAT'
];

ledId.forEach(
    led => {
        console.log('set',led)
        $(`#${led}`).change(
            function(){
                console.log('send',$(this).prop('checked'))
                socket.send(
                    JSON.stringify({
                        type : 'LED CONTROL',
                        id : led,
                        state : $(this).prop('checked'),
                        update : false
                    })
                );
            }
        )
    }
);
let counter = 0
const interval = setInterval(function() {
    counter++;
    console.log(counter);
    if(counter === 5){
        clearInterval(interval)
    }
    if(counter % 2 === 0){
        $('#LLIV').bootstrapToggle('on')
    }else{
        $('#LLIV').bootstrapToggle('off')
    }
},500)