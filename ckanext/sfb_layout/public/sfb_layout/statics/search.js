$(document).ready(function(){
    const $searchType = $('#search-type-dropdown');
    const selectedSearchType = $('#selected_search_type').val();
    if ($searchType.length) {
        $searchType.select2({ width: '100%' });
        $searchType.val(selectedSearchType).trigger('change');
    }

    $('.search-form').on('submit', function(e){
        const $form = $(this);
        const $dropdown = $form.find('#search-type-dropdown');
        if($dropdown.length){
            e.preventDefault();
            const searchType = $dropdown.val();
            const searchPhrase = $form.find('#field-giant-search-mimic').val();
            const query = searchType !== '0' ? searchType + ':' + searchPhrase : searchPhrase;
            $form.find('#field-giant-search').val(query);
            this.submit();
        }
    });
});
