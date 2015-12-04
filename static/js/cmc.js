$(document).ready(function(){



    $('#loadingModules').hide();
    $('#loadingEqtls').hide();

    $('#module-show-button').click(function(){

        $(document).off(".eqtlCall");
        $(document).on('ajaxStart.moduleCall', function(){
            $('#loadingModules').show();
        });
        $(document).on("ajaxStop.moduleCall", function(){
            $('#loadingModules').hide();
        });

        var moduleId;
        moduleId = $(this).attr('data-module-id');
        $.get('/viz/async_module_load/', {module_name: moduleId}, function(data){
            $('#module-collapsable-table').html(data);

        });
    });

    $('#eqtl-show-button').click(function(){

        $(document).off(".moduleCall");
        $(document).on('ajaxStart.eqtlCall', function(){
            $('#loadingEqtls').show();
        });
        $(document).on("ajaxStop.eqtlCall", function(){
            $('#loadingEqtls').hide();
        });

        var geneId;
        geneId = $(this).attr('data-gene-id');
        $.get('/viz/async_eqtl_load/', {gene_obj_id: geneId}, function(data){
            $('#eqtl-collapsable-table').html(data);
        });
    });

    var table = $('#eqtl-collapsable-table').stupidtable();

    table.on("beforetablesort", function (event, data) {
      // Apply a "disabled" look to the table while sorting.
      // Using addClass for "testing" as it takes slightly longer to render.
      $("#msg").text("Sorting...");
      $("table").addClass("disabled");
    });

    table.on("aftertablesort", function (event, data) {
      // Reset loading message.
      $("#msg").html("&nbsp;");
      $("table").removeClass("disabled");
      var th = $(this).find("th");
      th.find(".arrow").remove();
      var dir = $.fn.stupidtable.dir;
      var arrow = data.direction === dir.ASC ? "&uarr;" : "&darr;";
      th.eq(data.column).append('<span class="arrow">' + arrow +'</span>');
    });

    var table = $('#diff-expression-table').stupidtable();

    table.on("beforetablesort", function (event, data) {
      // Apply a "disabled" look to the table while sorting.
      // Using addClass for "testing" as it takes slightly longer to render.
      $("#msg").text("Sorting...");
      $("table").addClass("disabled");
    });

    table.on("aftertablesort", function (event, data) {
      // Reset loading message.
      $("#msg").html("&nbsp;");
      $("table").removeClass("disabled");
      var th = $(this).find("th");
      th.find(".arrow").remove();
      var dir = $.fn.stupidtable.dir;
      var arrow = data.direction === dir.ASC ? "&uarr;" : "&darr;";
      th.eq(data.column).append('<span class="arrow">' + arrow +'</span>');
    });



});