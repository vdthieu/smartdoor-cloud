let dataTable = jQuery('#data-table > tbody:last-child');

function getTable (){
    socket.send(JSON.stringify({
    type : "GET TABLE",
    time : (new Date()).toUTCString()
}));
}

function appendDataTable (data){
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