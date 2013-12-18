class TwittersController < ApplicationController
	def new
		render "new"
	end

	def create 
		@tweet = Twitter.new(params[:tweet])
		@tweet.save
		redirect_to @tweet
		render text: params[:tweet].inspect
	end
end
