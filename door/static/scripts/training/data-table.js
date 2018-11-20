let dataTable = jQuery('#bootstrap-data-table-export > tbody:last-child');

function getTable (){
    socket.send(JSON.stringify({
    type : "GET TABLE",
    time : (new Date()).toUTCString()
}));
}

function appendDataTable (data){
    let dataTable = jQuery('#bootstrap-data-table-export > tbody:last-child');
    data.forEach(
        (item,index) => {
            const value =
                `<tr>
                    <th scope="row">${index}</th>
                    <td>${item.time}</td>
                    <td>${item.id}</td>
                    <td>${item.state}</td>
                </tr>`;
            dataTable.append(value);
        }
    )
}

function unshiftDataTable (data){
    const table = jQuery('#bootstrap-data-table-export > tbody> tr>th');
    for(let i=0;i<table.length;i++){
        let item = jQuery(table[i])
        item.text(parseInt(item.text()) + 1)
    }

    jQuery('#bootstrap-data-table-export > tbody> tr:first').before(
         `<tr>
                <th scope="row">0</th>
                <td>${data.time}</td>
                <td>${data.id}</td>
                <td>${data.state + 0}</td>
            </tr>`
    )
}