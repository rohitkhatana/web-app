class TwittersController < ApplicationController
	def new
		render "new"
	end


	def create 
		@tweet = Twitter.new(params[:tweet])
		@tweet.save
		redirect_to @tweet
		#render text: params[:tweet].inspect
	end


	def facets
		@sea = Twitter.search do 
			facet 'word', :global => true do
        		terms :tweet
      		end
			#facet('word') {}
		end

		if @sea
			p "sae exists "
			p "#{@sea.facets['word']['terms'][0]['term']}"
			p "#{@sea.facets['word']['terms'][0]['count']}"
		else
			p "try hasd "
		end		
	end
	#end

	def show
		@tweet = Twitter.find(params[:id])
		if @tweet
			p "tweet exit"
		else 
			p "not exits"
		end
		#@sea = Twitter.search(params)#all #search(:facet => { })

		@sea = Twitter.search do 
			facet 'word', :global => true do
        		terms :tweet
      		end
			#facet('word') {}
		end

		if @sea
			p "sae exists "
			p "#{@sea.facets['word']['terms'][0]['term']}"
			p "#{@sea.facets['word']['terms'][0]['count']}"
		else
			p "try hasd "
		end		
end
end