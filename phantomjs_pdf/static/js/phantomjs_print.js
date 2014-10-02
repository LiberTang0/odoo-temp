/**
 * Created by colin on 22/09/14.
 */
/**
 * Created by colin on 06/05/14.
 */
var page = require('webpage').create(),
    system = require('system'),
    fileSystem = require('fs'),
    address,
    login_details,
    outputFile,
    output = {},
    database;
//1: url to visit 2: login details
address = system.args[1];
login_details = system.args[2];
database = system.args[3];
outputFile = system.args[4];
//page.customHeaders={'Authorization': 'Basic '+login_details};
output['errors'] = new Array();
output['file_name'] = "";
output['msg'] = new Array();


page.paperSize = {
    format: 'A4',
    margin: {left:"1cm", right:"1cm", top:"1cm", bottom:"0cm"},
    width: "21cm",
    height: "29.7cm",
    orientation: 'portrait',
    footer:{
        height: "1cm",
        contents: phantom.callback(function(pageNum, numPages){
            return "<div style='width: 18cm; font-size: 6pt; font-family: sans-serif;  padding-left: 1cm; padding-right: 1cm;'><div style='float: left; padding-right: 1.2cm;'><p><strong>REF:</strong> </p></div><div style='float: right; padding-left: 1.2cm'><p>Page "+pageNum+" of "+numPages+"</p></div></div>";
        })
    }
}

page.onConsoleMessage = function(message, lineNum, sourceId){
    var message_dict = {
        'message': message,
        'line': lineNum,
        'sourceId': sourceId
    }
    output['msg'].push(message_dict);
};

page.onError = function(msg, trace) {

    var error_dict = {
        'message': msg,
        'items': new Array()
    }

    trace.forEach(function(item) {
        error_dict['items'].push({'line': item.line, 'file': item.file });
    });

    output['errors'].push(error_dict);
}


page.open('http://localhost:8169/login?db='+database+'&login='+login_details+'&key='+login_details+'&redirect='+encodeURIComponent(address), function(status){

    if(status=="success") {

        if (page.evaluate(function () {
            return typeof PhantomJSPrinting == "object";
        })) {
            paperSize = page.paperSize;
            paperSize.footer.height = page.evaluate(function () {
                return PhantomJSPrinting.footer.height;
            });
            paperSize.footer.contents = phantom.callback(function (pageNum, numPages) {
                return page.evaluate(function (pageNum, numPages) {
                    return PhantomJSPrinting.footer.contents(pageNum, numPages);
                }, pageNum, numPages);
            });
            page.paperSize = paperSize;
        }

        var table_fix = page.evaluate(function () {

            var debug = true;
            var page_height = 1154;
            var page_margin = 37;
            var mod_delta = 0;
            var d = [];

            jQuery('.page').first().find('.row').each(function (i) {
                var h3_height = 0;//jQuery(this).find('h3').first().height() + parseInt(jQuery(this).find('h3').first().css('margin-bottom').replace('px',''));
                var start = jQuery(this).position().top;
                if ((page_height - start % page_height) < (h3_height + 52) && i != 0) {
                    jQuery(this).css('margin-top', (page_height - (start % page_height)));
                    mod_delta = 0;
                }
                var end = start + jQuery(this).height();
                var mod = end % page_height;

                if (mod < mod_delta || jQuery(this).height() > page_height) {
                    var tr_mod_delta = mod_delta;

                    jQuery(this).find('.main-entry').each(function (j, el) {
                        var tr_start = jQuery(el).position().top;
                        if (tr_start % page_height < 52) {
                            jQuery(el).children().css('padding-top', (52 - (tr_start % page_height)));
                        }
                        var tr_end = tr_start + jQuery(this).height();
                        var tr_mod = tr_end % page_height;
                        var offset = i == 0 ? 0 : 52;
                        if (tr_mod < tr_mod_delta) {
                            if (j % 2 == 0) {
                                if (j == 0) {
                                    jQuery(el).parent().css('margin-top', (page_height - (tr_start % page_height)));
                                    mod_delta = 0;
                                    tr_mod_delta = 0;
                                } else {
                                    jQuery(el).children().css('padding-top', ((page_height - (tr_start % page_height)) + offset) + 'px');
                                }
                            } else {
                                jQuery(el).prev('.main-entry').children().css('padding-bottom', ((page_height - (tr_start % page_height)) + offset) + 'px');
                            }
                        }
                        tr_mod_delta = tr_mod;
                    });
                }
                mod_delta = mod;
            });
            return;
        });


        window.setTimeout(function () {
            if (fileSystem.exists(outputFile)) {
                fileSystem.remove(outputFile);
            }
            page.render(outputFile);
            output['file_name'] = outputFile;


            console.log(JSON.stringify(output));
            phantom.exit();
        });
    }else{
        output['errors'].push({'message': 'page did not open properly', 'items': []})
        console.log(JSON.stringify(output));
        phantom.exit();
    }
});